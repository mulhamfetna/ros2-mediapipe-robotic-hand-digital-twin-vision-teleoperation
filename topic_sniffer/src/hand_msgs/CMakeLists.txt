cmake_minimum_required(VERSION 3.8)
project(hand_msgs)

find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  msg/JointAngles.msg
)