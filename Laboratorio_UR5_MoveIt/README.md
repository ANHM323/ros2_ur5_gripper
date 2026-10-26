# Laboratorio UR5 + gripper — ROS 2 Jazzy, Gazebo, URSim y MoveIt

Workspace independiente dentro de `ros_course_ws`, basado en
[ur5_gripper_packages](https://github.com/DanielPalominoS/ur5_gripper_packages).

## Paquetes (`src/`)
| Paquete | Contenido |
|---|---|
| `ur5_robotiq_description` | URDF/XACRO UR5 + gripper simple (del curso). Se agregó `ur5_gripper_ursim.urdf.xacro` (UR5 del driver oficial + gripper). |
| `ur5_robotiq_bringup` | Simulación en Gazebo Harmonic + ros2_control (del curso). |
| `ur5_pick_place` | **Nodos Pick and Place**: `pick_place_node` (Gazebo, E/S por tópicos) y `pick_place_ursim` (URSim/robot real, E/S reales del UR). `gripper_tool_io` refleja la salida de herramienta TO0 en la pinza de RViz. Launch `ur5_ursim.launch.py`. |
| `ur5_robotiq_moveit_config` | Paquete generado con **MoveIt Setup Assistant** (grupos `ur_arm` y `gripper`, poses `home/ready/open/close`, efector `arm_eef`). |
| `ur5_moveit_nodo` | Nodo C++ con `MoveGroupInterface` que planifica y ejecuta trayectorias (poses nombradas, articulares y cartesianas). |

## Compilar
```bash
cd ~/ros_course_ws/Laboratorio_UR5_MoveIt
source /opt/ros/jazzy/setup.bash
colcon build && source install/setup.bash
```

## 1. Simulación Gazebo + control por tópicos
```bash
ros2 launch ur5_robotiq_bringup sim_gz_sgb.launch.py
ros2 topic pub --once /scaled_joint_trajectory_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{joint_names: [shoulder_pan_joint, shoulder_lift_joint, elbow_joint, wrist_1_joint, wrist_2_joint, wrist_3_joint], points: [{positions: [1.2, -1.2, 1.2, -1.57, -1.57, 0.5], time_from_start: {sec: 3}}]}"
ros2 topic pub --once /gripper_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.004, 0.004]}"
```

## 2. Pick and Place
**Gazebo** (E/S simuladas por tópicos):
```bash
ros2 run ur5_pick_place pick_place_node
ros2 topic echo /io/do_pieza_entregada                                     # salida digital
ros2 topic pub --once /io/di_pieza_presente std_msgs/msg/Bool "{data: true}" # entrada digital
```
**URSim (tablet PolyScope, conexión por IP)**:
```bash
ros2 run ur_client_library start_ursim.sh -m ur5 -f "-p 6080:6080 -p 5900:5900 -p 30001-30004:30001-30004 -p 29999:29999"
# Tablet: http://localhost:6080/vnc.html  -> programa con nodo External Control (Host IP 192.168.56.1), Play
ros2 launch ur5_pick_place ur5_ursim.launch.py robot_ip:=192.168.56.101
ros2 run ur5_pick_place pick_place_ursim
ros2 service call /io_and_status_controller/set_io ur_msgs/srv/SetIO "{fun: 1, pin: 0, state: 1.0}"  # sensor de pieza
```
| Operación | Implementación (URSim) |
|---|---|
| Gripper abrir/cerrar | Salida de herramienta TO0 (pin 16) |
| Espera entrada digital | DI0 o DO0 (sensor simulado, ver nota) |
| Activación salida digital | DO1 = pieza entregada |
| Mensajes informativos | Log del nodo |

## 3. MoveIt
```bash
ros2 launch ur5_robotiq_moveit_config demo.launch.py   # planificación en RViz
ros2 run ur5_moveit_nodo ur5_moveit_nodo                # nodo con MoveGroupInterface
```

## Notas / problemas encontrados
- WSLg dejó de dibujar ventanas (RViz/Gazebo abiertos pero invisibles): se solucionó con `wsl --shutdown`.
- En URSim las E/S solo se pueden forzar desde la tablet en modo *Simulation*, pero en ese modo el robot no reporta movimiento al driver; se usa modo *Real Robot* y la entrada se simula con un servicio ROS.
- Los popups del `dashboard_client` pausan el movimiento con External Control; se reemplazaron por logs.
- Setup Assistant (Jazzy): `joint_limits.yaml` sin límites de aceleración y `initial_positions.yaml` fuera de límites del gripper: corregidos a mano. No se agregó virtual joint porque el XACRO ya tiene `world` como raíz. El gripper usa `JointTrajectoryController` (el `GripperActionController` solo admite un joint).
