# ROS2 UR5 + Gripper - Implementación Mínima

## Estructura del workspace (`ur5_sim_ws/src`)
```bash
pick_place_pkg              # Nodo rutina Pick and Place
ros2_robotiq_gripper         # Control gripper
ur5_gripper_description      # Modelo UR5 + gripper (urdf/ .xacro)
ur5_gripper_moveit_config    # Configuración MoveIt
```

## Eliminado / Respaldado
- `Universal_Robots_ROS2_Description` (104 MB) -> `src_backup/`
- `Universal_Robots_ROS2_GZ_Simulation` (1.7 MB) -> `src_backup/`

Nota: los symlinks en `install/` pueden romperse al respaldar. Solución: reemplazar con archivos reales desde `src_backup/`.

## Archivo del modelo (simulación)
- Fuente: `ur5_gripper_description/urdf/ur5_with_gripper_sim.urdf.xacro`
- Compilado en: `install/ur5_gripper_description/share/ur5_gripper_description/urdf/ur5_with_gripper_sim.urdf.xacro`

## Comando para lanzar simulador (Gazebo / RViz / MoveIt)
```bash
# Entrar al distrobox
docker exec -it ros2-jazzy bash

# Configurar entorno
source /opt/ros/jazzy/setup.bash
source /home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/setup.bash

# Lanzar simulador (archivo .launch.py, NO .urdf.xacro)
ros2 launch ur_simulation_gz ur_sim_control.launch.py \
  ur_type:=ur5 \
  description_file:=/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/ur5_gripper_description/share/ur5_gripper_description/urdf/ur5_with_gripper_sim.urdf.xacro \
  controllers_file:=/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/ur5_gripper_description/share/ur5_gripper_description/config/controllers_ur5_gripper.yaml \
  gazebo_gui:=false launch_rviz:=false
```

Nota: el `.urdf.xacro` va como argumento (`description_file:=`), NO como archivo de `ros2 launch`.

## Errores comunes y solución
| Error | Causa | Solución |
|---|---|---|
`FileNotFoundError: ur_sim_control.launch.py` | `Universal_Robots_ROS2_GZ_Simulation` respaldado | Restaurar archivo `.launch.py` en `install/ur_simulation_gz/share/ur_simulation_gz/launch/` |
`No such file or directory: ur_macro.xacro` | Symlink roto en `install/ur_description/share/ur_description/urdf/` | Copiar archivos `.xacro` y `inc/*.xacro` desde `src_backup/Universal_Robots_ROS2_Description/urdf/` |
`visual_parameters.yaml` no encontrado | Symlink roto en `install/ur_description/share/ur_description/config/ur5/` | Copiar archivos `config/ur5/*.yaml` y `config/initial_positions.yaml` desde `src_backup/` |

## Estado actual del contenedor
- `ros2-jazzy` (ubuntu:24.04, distrobox, usuario `andyh` igual al host)
- `ros2_ws` principal tiene `turtlesim`
- `ur5_sim_ws` tiene los 4 paquetes mínimos compilados en `install/`
- `robot_state_publisher` ya corrió con `ur5_with_gripper_sim.urdf.xacro`

## Repositorios / archivos clave
- Modelo: `/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/src/ur5_gripper_description/urdf/ur5_with_gripper_sim.urdf.xacro`
- Nodo Pick/Place: `/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/src/pick_place_pkg/pick_place_pkg/pick_place_node.py`
- Configuración MoveIt: `/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/src/ur5_gripper_moveit_config/`
- Workspace compilado: `/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/install/`
- Respaldo: `/home/andyh/distrobox-homes/ros2-jazzy/ur5_sim_ws/src_backup/`
