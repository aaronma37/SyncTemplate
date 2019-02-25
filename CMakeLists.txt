cmake_minimum_required(VERSION 2.8.3)
project(SyncTemplate)


find_package(catkin REQUIRED COMPONENTS
  std_msgs
  rospy
  message_generation
)


include_directories(
  ${catkin_INCLUDE_DIRS}
)


add_message_files(
	FILES
	TwoScalarMsg.msg
	AckMsg.msg
	rto_derp_msg.msg
	)


generate_messages(
  DEPENDENCIES
  std_msgs

)


catkin_package(

   CATKIN_DEPENDS message_runtime
)



file(GLOB_RECURSE HEADER_FILES include/*.h)


  #catkin_install_python(PROGRAMS
  #  src/main.py
  #  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
  #)





