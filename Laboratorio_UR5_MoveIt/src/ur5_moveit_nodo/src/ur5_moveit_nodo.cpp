// Nodo que usa MoveIt (MoveGroupInterface) para planificar y ejecutar trayectorias
// del UR5 con gripper, usando la configuracion generada con el MoveIt Setup Assistant
// (paquete ur5_robotiq_moveit_config: grupos ur_arm y gripper, poses home/ready/open/close).
#include <memory>
#include <thread>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>

using moveit::planning_interface::MoveGroupInterface;

static bool planificar_y_ejecutar(MoveGroupInterface & grupo, const rclcpp::Logger & log,
                                  const std::string & desc)
{
  MoveGroupInterface::Plan plan;
  RCLCPP_INFO(log, "Planificando: %s", desc.c_str());
  if (!static_cast<bool>(grupo.plan(plan))) {
    RCLCPP_ERROR(log, "Fallo la planificacion: %s", desc.c_str());
    return false;
  }
  RCLCPP_INFO(log, "Plan OK (%zu puntos, %.2f s). Ejecutando...",
    plan.trajectory.joint_trajectory.points.size(),
    rclcpp::Duration(plan.trajectory.joint_trajectory.points.back().time_from_start).seconds());
  return static_cast<bool>(grupo.execute(plan));
}

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>(
    "ur5_moveit_nodo",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto log = node->get_logger();

  rclcpp::executors::SingleThreadedExecutor exec;
  exec.add_node(node);
  std::thread spinner([&exec]() {exec.spin();});

  // Grupos definidos en el Setup Assistant
  MoveGroupInterface brazo(node, "ur_arm");
  MoveGroupInterface pinza(node, "gripper");
  brazo.setMaxVelocityScalingFactor(0.3);
  brazo.setMaxAccelerationScalingFactor(0.3);
  brazo.setPlanningTime(5.0);
  brazo.setNumPlanningAttempts(5);

  RCLCPP_INFO(log, "Planning frame: %s | Efector: %s",
    brazo.getPlanningFrame().c_str(), brazo.getEndEffectorLink().c_str());

  // 1) Pose nombrada "home" y abrir pinza
  brazo.setNamedTarget("home");
  planificar_y_ejecutar(brazo, log, "brazo -> home (pose nombrada)");
  pinza.setNamedTarget("open");
  planificar_y_ejecutar(pinza, log, "gripper -> open");

  // 2) Objetivo articular (zona de pick)
  brazo.setJointValueTarget(std::vector<double>{0.8, -1.3, 1.6, -1.87, -1.57, 0.0});
  planificar_y_ejecutar(brazo, log, "brazo -> objetivo articular (aproximacion)");

  // 3) Objetivo cartesiano: bajar 10 cm desde la pose actual
  auto pose = brazo.getCurrentPose().pose;
  pose.position.z -= 0.10;
  brazo.setPoseTarget(pose);
  planificar_y_ejecutar(brazo, log, "brazo -> bajar 10 cm (objetivo cartesiano)");

  // 4) Cerrar pinza (tomar pieza) y subir
  pinza.setNamedTarget("close");
  planificar_y_ejecutar(pinza, log, "gripper -> close");
  pose.position.z += 0.10;
  brazo.setPoseTarget(pose);
  planificar_y_ejecutar(brazo, log, "brazo -> subir 10 cm");

  // 5) Llevar a "ready", abrir y volver a "home"
  brazo.setNamedTarget("ready");
  planificar_y_ejecutar(brazo, log, "brazo -> ready (pose nombrada)");
  pinza.setNamedTarget("open");
  planificar_y_ejecutar(pinza, log, "gripper -> open");
  brazo.setNamedTarget("home");
  planificar_y_ejecutar(brazo, log, "brazo -> home");

  RCLCPP_INFO(log, "Secuencia MoveIt terminada");
  rclcpp::shutdown();
  spinner.join();
  return 0;
}
