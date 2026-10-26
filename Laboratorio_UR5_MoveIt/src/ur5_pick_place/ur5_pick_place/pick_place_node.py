"""Nodo que simula una rutina Pick and Place con el UR5 + gripper simple.

Puntos de interes: home, pick (con aproximacion) y place (con aproximacion).
Operaciones: mensajes informativos, apertura/cierre del gripper,
espera de entrada digital (topico /io/di_pieza_presente) y
activacion de salida digital (topico /io/do_pieza_entregada).
"""
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import Bool, Float64MultiArray, String
from trajectory_msgs.msg import JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from builtin_interfaces.msg import Duration

JOINTS = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
          'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']

# Puntos de interes (rad). lift + elbow + wrist_1 = -pi/2 -> herramienta hacia abajo
POSES = {
    'home':        [0.00, -1.57, 1.57, -1.57, -1.57, 0.0],
    'pick_aprox':  [0.00, -1.50, 1.40, -1.47, -1.57, 0.0],
    'pick':        [0.00, -1.30, 1.60, -1.87, -1.57, 0.0],
    'place_aprox': [1.57, -1.50, 1.40, -1.47, -1.57, 0.0],
    'place':       [1.57, -1.30, 1.60, -1.87, -1.57, 0.0],
}
GRIPPER_ABIERTO = [0.04, 0.04]
GRIPPER_CERRADO = [0.004, 0.004]


class PickPlace(Node):
    def __init__(self):
        super().__init__('pick_place_node')
        self.declare_parameter('ciclos', 1)
        self.declare_parameter('t_mov', 3.0)

        self.arm = ActionClient(
            self, FollowJointTrajectory,
            '/scaled_joint_trajectory_controller/follow_joint_trajectory')
        self.pub_gripper = self.create_publisher(
            Float64MultiArray, '/gripper_controller/commands', 10)
        self.pub_do = self.create_publisher(Bool, '/io/do_pieza_entregada', 10)
        self.pub_estado = self.create_publisher(String, '/pick_place/estado', 10)

        self.di = False
        self.create_subscription(Bool, '/io/di_pieza_presente', self.cb_di, 10)

    # ---------- utilidades ----------
    def cb_di(self, msg):
        self.di = msg.data

    def info(self, texto):
        self.get_logger().info(texto)
        self.pub_estado.publish(String(data=texto))

    def mover(self, nombre):
        t = float(self.get_parameter('t_mov').value)
        self.info(f'Moviendo a "{nombre}"')
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINTS
        p = JointTrajectoryPoint()
        p.positions = POSES[nombre]
        p.time_from_start = Duration(sec=int(t), nanosec=int((t % 1) * 1e9))
        goal.trajectory.points = [p]

        fut = self.arm.send_goal_async(goal)
        while not fut.done():
            time.sleep(0.05)
        handle = fut.result()
        if not handle.accepted:
            self.get_logger().error('Trayectoria rechazada')
            return
        res = handle.get_result_async()
        while not res.done():
            time.sleep(0.05)
        code = res.result().result.error_code
        if code != 0:
            self.get_logger().warn(f'Resultado con error_code={code}')

    def gripper(self, valores, texto):
        self.info(texto)
        self.pub_gripper.publish(Float64MultiArray(data=valores))
        time.sleep(1.5)

    def esperar_di(self):
        self.info('Esperando entrada digital /io/di_pieza_presente = true ...')
        while rclpy.ok() and not self.di:
            time.sleep(0.1)
        self.di = False  # se consume la senal
        self.info('Entrada digital recibida')

    def salida_do(self, valor):
        self.pub_do.publish(Bool(data=valor))
        self.info(f'Salida digital /io/do_pieza_entregada = {valor}')

    # ---------- rutina ----------
    def rutina(self):
        self.info('Esperando servidor de accion del brazo...')
        if not self.arm.wait_for_server(timeout_sec=15.0):
            self.get_logger().error('Controlador del brazo no disponible. ¿Lanzaste la simulacion?')
            return

        for ciclo in range(int(self.get_parameter('ciclos').value)):
            self.info(f'===== Ciclo {ciclo + 1} =====')
            # Punto 1: HOME
            self.mover('home')
            self.gripper(GRIPPER_ABIERTO, 'Abriendo gripper')
            self.salida_do(False)

            # Punto 2: PICK
            self.mover('pick_aprox')
            self.esperar_di()
            self.mover('pick')
            self.gripper(GRIPPER_CERRADO, 'Cerrando gripper (pieza tomada)')
            self.mover('pick_aprox')

            # Punto 3: PLACE
            self.mover('place_aprox')
            self.mover('place')
            self.gripper(GRIPPER_ABIERTO, 'Abriendo gripper (pieza depositada)')
            self.salida_do(True)
            self.mover('place_aprox')

            # Regreso
            self.mover('home')
            self.info('Ciclo terminado')
        self.info('Rutina pick and place finalizada')


def main(args=None):
    rclpy.init(args=args)
    node = PickPlace()
    ex = MultiThreadedExecutor()
    ex.add_node(node)
    hilo = threading.Thread(target=ex.spin, daemon=True)
    hilo.start()
    try:
        node.rutina()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
