cmake_minimum_required(VERSION 3.30)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

include(FetchContent)
set(FETCHCONTENT_UPDATES_DISCONNECTED TRUE)
FetchContent_Declare(ftxui
  GIT_REPOSITORY https://github.com/ArthurSonzogni/ftxui
  GIT_TAG main # Important: Specify a version or a commit hash here.
)
FetchContent_MakeAvailable(ftxui)

project(vm)
add_executable(vm vm.cpp built_ins.cpp vm_interactive.cpp scheme_objects.cpp)
target_link_libraries(vm
  PRIVATE ftxui::screen
  PRIVATE ftxui::dom
  PRIVATE ftxui::component
)