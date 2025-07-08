// LoginWindow.h

#ifndef LOGINWINDOW_H
#define LOGINWINDOW_H

#include <QWidget>

// 前向声明，避免循环包含
class QLineEdit;
class QPushButton;
class QLabel;
class MainWindow;

class LoginWindow : public QWidget
{
    Q_OBJECT

public:
    explicit LoginWindow(QWidget *parent = nullptr);
    ~LoginWindow();

private slots:
    void onLoginClicked();

private:
    void setupUi();

    // UI 组件
    QLabel *titleLabel;
    QLineEdit *usernameEdit;
    QLineEdit *passwordEdit;
    QPushButton *loginButton;
    QLabel *statusLabel;

    // 主窗口指针
    MainWindow *mainWindow;
};

#endif // LOGINWINDOW_H
