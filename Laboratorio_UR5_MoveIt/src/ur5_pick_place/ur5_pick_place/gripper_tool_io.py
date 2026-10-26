"""Refleja la salida de herramienta TO0 del UR (URSim/real) en los dedos del gripper simple.

TO0 = 1 -> gripper cerrado, TO0 = 0 -> gripper abierto. Publica /joint_states
para que robot_state_publisher y RViz muestren la pinza.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from ur_msgs.msg import IOStates

ABIERTO, CERRADO = 0.04, 0.004
PIN_TOOL = 16


class GripperToolIO(Node):
    def __init__(self):
        super().__init__('gripper_tool_io')
        self.pos = ABIERTO
        self.objetivo = ABIERTO
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        self.create_subscription(IOStates, '/io_and_status_controller/io_states', self.cb, 10)
        self.create_timer(0.05, self.publicar)

    def cb(self, msg):
        for p in msg.digital_out_states:
            if p.pin == PIN_TOOL:
                nuevo = CERRADO if p.state else ABIERTO
                if nuevo != self.objetivo:
                    self.get_logger().info('Gripper ' + ('CERRADO' if p.state else 'ABIERTO') + ' (TO0)')
                self.objetivo = nuevo

    def publicar(self):
        # movimiento suave de los dedos
        paso = 0.003
        d = self.objetivo - self.pos
        self.pos += max(-paso, min(paso, d))
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = ['gripper_finger_joint', 'right_finger_joint']
        js.position = [self.pos, self.pos]
        self.pub.publish(js)


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(GripperToolIO())


if __name__ == '__main__':
    main()
