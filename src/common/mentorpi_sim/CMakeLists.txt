cmake_minimum_required(VERSION 3.8)
project(mentorpi_sim)
 
find_package(ament_cmake REQUIRED)
 
install(DIRECTORY launch worlds config rviz
  DESTINATION share/${PROJECT_NAME})
 
ament_package()