# CMakeLists.txt

cmake_minimum_required(VERSION 3.16)
project(ParkinsonRecognitionSystem VERSION 1.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 自动处理 Qt 的 MOC, UIC, RCC
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# 查找 Qt6 包，并指定需要的模块
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)

# 定义可执行文件及其源文件
add_executable(ParkinsonRecognitionSystem
    main.cpp
    LoginWindow.h
    LoginWindow.cpp
    MainWindow.h
    MainWindow.cpp
)

# 链接 Qt6 库
target_link_libraries(ParkinsonRecognitionSystem PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
)

