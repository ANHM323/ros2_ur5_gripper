# ROS2 UR5 + Gripper - Implementación Mínima

Workspace simplificado con los paquetes mínimos para simular y controlar un UR5 con gripper robotiq_85 en ROS2 Jazzy.

## Paquetes incluidos
- `pick_place_pkg` - Nodo de rutina Pick and Place (3 puntos, gripper, entradas/salidas)
- `ur5_gripper_description` - Modelo URDF (`ur5_with_gripper_sim.urdf.xacro`)
- `ros2_robotiq_gripper` - Control del gripper
- `ur5_gripper_moveit_config` - Configuración MoveIt

## Archivo de referencia
- `ROS2_UR5_GRIPPER_MINIMO.md` - Documentación completa (simulador, errores, comandos, estructura)

## Lanzar simulador
```bash
docker exec -it ros2-jazzy bash
source /opt/ros/jazzy/setup.bash
source /home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/setup.bash
ros2 launch ur_simulation_gz ur_sim_control.launch.py \
  ur_type:=ur5 \
  description_file:=/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/ur5_gripper_description/share/ur5_gripper_description/urdf/ur5_with_gripper_sim.urdf.xacro \
  controllers_file:=/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/ur5_gripper_description/share/ur5_gripper_description/config/controllers_ur5_gripper.yaml \
  gazebo_gui:=false launch_rviz:=false
```

## Usuario / Autor
- `ANHM323`
- `andyh@escuelaing.edu.co`
