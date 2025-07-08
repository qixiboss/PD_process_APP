// LoginWindow.cpp

#include "LoginWindow.h"
#include "MainWindow.h" // 包含主窗口头文件
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QMessageBox>

LoginWindow::LoginWindow(QWidget *parent)
    : QWidget(parent), mainWindow(nullptr)
{
    setupUi();
    setWindowTitle("系统登录");
    setFixedSize(350, 200); // 固定窗口大小
}

LoginWindow::~LoginWindow()
{
    // mainWindow 的所有权在登录成功后已转移，此处无需 delete
}

void LoginWindow::setupUi()
{
    // 初始化 UI 组件
    titleLabel = new QLabel("帕金森识别系统登录", this);
    titleLabel->setAlignment(Qt::AlignCenter);
    QFont titleFont = titleLabel->font();
    titleFont.setPointSize(16);
    titleFont.setBold(true);
    titleLabel->setFont(titleFont);

    usernameEdit = new QLineEdit(this);
    usernameEdit->setPlaceholderText("用户名");

    passwordEdit = new QLineEdit(this);
    passwordEdit->setPlaceholderText("密码");
    passwordEdit->setEchoMode(QLineEdit::Password);

    loginButton = new QPushButton("登录", this);
    statusLabel = new QLabel(this);
    statusLabel->setAlignment(Qt::AlignCenter);
    statusLabel->setStyleSheet("color: red;");

    // 布局
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    mainLayout->addWidget(titleLabel);
    mainLayout->addSpacing(10);
    mainLayout->addWidget(usernameEdit);
    mainLayout->addWidget(passwordEdit);
    mainLayout->addWidget(loginButton);
    mainLayout->addWidget(statusLabel);
    mainLayout->addStretch();

    setLayout(mainLayout);

    // 连接信号和槽
    connect(loginButton, &QPushButton::clicked, this, &LoginWindow::onLoginClicked);
    // 按下回车键也能触发登录
    connect(passwordEdit, &QLineEdit::returnPressed, this, &LoginWindow::onLoginClicked);
}

void LoginWindow::onLoginClicked()
{
    // 硬编码的用户名和密码
    const QString correctUsername = "admin";
    const QString correctPassword = "password";

    if (usernameEdit->text() == correctUsername && passwordEdit->text() == correctPassword) {
        // 登录成功
        // 创建并显示主窗口
        mainWindow = new MainWindow();
        mainWindow->show();
        // 关闭当前登录窗口
        this->close();
    } else {
        // 登录失败
        QMessageBox::warning(this, "登录失败", "用户名或密码错误！");
        passwordEdit->clear();
        statusLabel->setText("用户名或密码错误！");
    }
}
