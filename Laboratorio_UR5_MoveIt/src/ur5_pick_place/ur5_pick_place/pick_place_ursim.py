"""Rutina Pick and Place para el UR5 en URSim (PolyScope) via ur_robot_driver.

Operaciones en cada punto:
  - Mensajes informativos: log de ROS (los popups del dashboard pausan el robot en PolyScope).
  - Gripper: salida digital de herramienta TO0 (1 = cerrar, 0 = abrir).
  - Espera de entrada digital: DI0 del robot (se activa desde la pestana E/S).
  - Salida digital: DO1 = "pieza entregada".
"""
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from ur_msgs.srv import SetIO
from ur_msgs.msg import IOStates
from ur_dashboard_msgs.srv import Popup
from std_srvs.srv import Trigger

JOINTS = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
          'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']

POSES = {
    'home':        [0.00, -1.57, 1.57, -1.57, -1.57, 0.0],
    'pick_aprox':  [0.00, -1.50, 1.40, -1.47, -1.57, 0.0],
    'pick':        [0.00, -1.30, 1.60, -1.87, -1.57, 0.0],
    'place_aprox': [1.57, -1.50, 1.40, -1.47, -1.57, 0.0],
    'place':       [1.57, -1.30, 1.60, -1.87, -1.57, 0.0],
}

PIN_DI_SENSOR = 0     # DI0: sensor de pieza presente
PIN_DO_ENTREGA = 1    # DO1: pieza entregada
PIN_DO_SENSOR_SIM = 0  # DO0: boton del operador que simula el sensor (URSim)
PIN_TOOL_GRIPPER = 16  # TO0 (pines 16-17 = salidas de herramienta)


class PickPlaceURSim(Node):
    def __init__(self):
        super().__init__('pick_place_ursim')
        self.declare_parameter('t_mov', 4.0)
        self.declare_parameter('ciclos', 1)
        self.arm = ActionClient(
            self, FollowJointTrajectory,
            '/scaled_joint_trajectory_controller/follow_joint_trajectory')
        self.cli_io = self.create_client(SetIO, '/io_and_status_controller/set_io')
        self.cli_popup = self.create_client(Popup, '/dashboard_client/popup')
        self.cli_close = self.create_client(Trigger, '/dashboard_client/close_popup')
        self.di = [False] * 8
        self.do = [False] * 18
        self.create_subscription(IOStates, '/io_and_status_controller/io_states', self.cb_io, 10)

    # ---------- utilidades ----------
    def cb_io(self, msg):
        for p in msg.digital_in_states:
            if p.pin < 8:
                self.di[p.pin] = p.state
        for p in msg.digital_out_states:
            if p.pin < 18:
                self.do[p.pin] = p.state

    def esperar(self, fut):
        while not fut.done():
            time.sleep(0.05)
        return fut.result()

    def popup(self, texto, segundos=3.0):
        self.get_logger().info(texto)
        if self.cli_popup.service_is_ready():
            self.esperar(self.cli_popup.call_async(Popup.Request(message=texto)))
            time.sleep(segundos)
            if self.cli_close.service_is_ready():
                self.esperar(self.cli_close.call_async(Trigger.Request()))

    def set_io(self, pin, valor, desc):
        self.get_logger().info(f'{desc}: pin {pin} = {int(valor)}')
        req = SetIO.Request(fun=SetIO.Request.FUN_SET_DIGITAL_OUT, pin=pin,
                            state=1.0 if valor else 0.0)
        self.esperar(self.cli_io.call_async(req))
        time.sleep(0.8)

    def gripper(self, cerrar):
        self.set_io(PIN_TOOL_GRIPPER, cerrar,
                    'Cerrando gripper (TO0)' if cerrar else 'Abriendo gripper (TO0)')

    def mover(self, nombre):
        t = float(self.get_parameter('t_mov').value)
        self.get_logger().info(f'Moviendo a "{nombre}"')
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINTS
        p = JointTrajectoryPoint()
        p.positions = POSES[nombre]
        p.time_from_start = Duration(sec=int(t), nanosec=int((t % 1) * 1e9))
        goal.trajectory.points = [p]
        while True:
            handle = self.esperar(self.arm.send_goal_async(goal))
            if handle.accepted:
                break
            self.get_logger().warn('Programa External Control detenido: presione PLAY en la tablet...')
            time.sleep(2.0)
        fut = handle.get_result_async()
        limite = time.time() + t + 6.0
        while not fut.done() and time.time() < limite:
            time.sleep(0.05)
        if not fut.done():
            # el robot ya llego pero el controlador no confirmo: se continua
            self.get_logger().warn(f'Sin confirmacion de "{nombre}", continuando')
            handle.cancel_goal_async()
        elif fut.result().result.error_code != 0:
            self.get_logger().warn(f'error_code={fut.result().result.error_code}')

    def esperar_di(self, pin):
        # En URSim (modo Real Robot) las entradas no se pueden forzar desde la tablet,
        # por eso el boton del operador DO0 tambien representa el sensor de pieza.
        self.get_logger().info(f'Esperando sensor de pieza: DI{pin} o boton DO{PIN_DO_SENSOR_SIM} = ON (pestana I/O)...')
        while rclpy.ok() and not (self.di[pin] or self.do[PIN_DO_SENSOR_SIM]):
            time.sleep(0.1)
        self.get_logger().info('Sensor de pieza activado -> continuar')

    # ---------- rutina ----------
    def rutina(self):
        self.get_logger().info('Esperando driver UR...')
        if not self.arm.wait_for_server(timeout_sec=15.0) or not self.cli_io.wait_for_service(timeout_sec=10.0):
            self.get_logger().error('Driver no disponible. ¿ur_control.launch.py corriendo?')
            return
        self.cli_popup.wait_for_service(timeout_sec=3.0)
        self.cli_close.wait_for_service(timeout_sec=3.0)

        for c in range(int(self.get_parameter('ciclos').value)):
            # (un popup aqui pausa el movimiento en PolyScope: solo log)
            self.get_logger().info(f'===== Inicio rutina Pick and Place - ciclo {c + 1} =====')
            # Punto 1: HOME
            self.mover('home')
            self.gripper(False)
            self.set_io(PIN_DO_ENTREGA, False, 'Salida DO1 (pieza entregada)')
            self.set_io(PIN_DO_SENSOR_SIM, False, 'Reinicio sensor simulado DO0')
            # Punto 2: PICK
            self.mover('pick_aprox')
            self.esperar_di(PIN_DI_SENSOR)
            self.mover('pick')
            self.gripper(True)
            self.mover('pick_aprox')
            # Punto 3: PLACE
            self.mover('place_aprox')
            self.mover('place')
            self.gripper(False)
            self.set_io(PIN_DO_ENTREGA, True, 'Salida DO1 (pieza entregada)')
            self.mover('place_aprox')
            self.mover('home')
            self.get_logger().info('===== Pieza entregada - ciclo terminado =====')
        self.get_logger().info('Rutina finalizada')


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceURSim()
    ex = MultiThreadedExecutor()
    ex.add_node(node)
    threading.Thread(target=ex.spin, daemon=True).start()
    try:
        node.rutina()
    except (KeyboardInterrupt, SystemExit):
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
