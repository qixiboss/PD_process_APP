// main.cpp

#include <QApplication>
#include "LoginWindow.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    // 创建并显示登录窗口
    LoginWindow loginWindow;
    loginWindow.show();

    // 进入Qt事件循环
    return a.exec();
}
