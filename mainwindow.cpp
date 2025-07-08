// MainWindow.cpp

#include "MainWindow.h"
#include <QNetworkReply> // <<<<<<<<<<<<<<<< 在这里添加这一行 <<<<<<<<<<<<<<<<
#include <QVBoxLayout>
#include <QGridLayout>
#include <QGroupBox>
#include <QLabel>
#include <QPushButton>
#include <QFileDialog>
#include <QMessageBox>
#include <QNetworkRequest>
#include <QHttpMultiPart>
#include <QHttpPart>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QStatusBar>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setupUi();
    setWindowTitle("帕金森识别系统主页面");
    setMinimumSize(500, 400);

    // 初始化网络管理器
    networkManager = new QNetworkAccessManager(this);
    connect(networkManager, &QNetworkAccessManager::finished, this, &MainWindow::onAnalysisFinished);
}

MainWindow::~MainWindow()
{
}

void MainWindow::setupUi()
{
    QWidget *centralWidget = new QWidget(this);
    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);

    // --- 数据导入部分 ---
    QGroupBox *importGroup = new QGroupBox("1. 导入数据", this);
    QGridLayout *importLayout = new QGridLayout(importGroup);

    gaitVideoLabel = new QLabel("步态视频: 未选择", this);
    faceVideoLabel = new QLabel("面部视频: 未选择", this);
    audioLabel = new QLabel("语音文件: 未选择", this);

    gaitVideoButton = new QPushButton("选择步态视频", this);
    faceVideoButton = new QPushButton("选择面部视频", this);
    audioButton = new QPushButton("选择语音文件", this);

    importLayout->addWidget(gaitVideoLabel, 0, 0);
    importLayout->addWidget(gaitVideoButton, 0, 1);
    importLayout->addWidget(faceVideoLabel, 1, 0);
    importLayout->addWidget(faceVideoButton, 1, 1);
    importLayout->addWidget(audioLabel, 2, 0);
    importLayout->addWidget(audioButton, 2, 1);

    // --- 控制按钮部分 ---
    QGroupBox *controlGroup = new QGroupBox("2. 操作", this);
    QHBoxLayout *controlLayout = new QHBoxLayout(controlGroup);

    processDataButton = new QPushButton("处理数据", this);
    generateReportButton = new QPushButton("生成报告", this);
    pastReportsButton = new QPushButton("往期报告", this);

    generateReportButton->setEnabled(false); // 初始禁用

    controlLayout->addWidget(processDataButton);
    controlLayout->addWidget(generateReportButton);
    controlLayout->addWidget(pastReportsButton);

    mainLayout->addWidget(importGroup);
    mainLayout->addWidget(controlGroup);
    mainLayout->addStretch();

    setCentralWidget(centralWidget);
    statusBar(); // 创建状态栏

    // 连接信号和槽
    connect(gaitVideoButton, &QPushButton::clicked, this, &MainWindow::selectGaitVideo);
    connect(faceVideoButton, &QPushButton::clicked, this, &MainWindow::selectFaceVideo);
    connect(audioButton, &QPushButton::clicked, this, &MainWindow::selectAudio);
    connect(processDataButton, &QPushButton::clicked, this, &MainWindow::processData);
    connect(generateReportButton, &QPushButton::clicked, this, &MainWindow::generateReport);
    connect(pastReportsButton, &QPushButton::clicked, this, &MainWindow::showPastReports);
}

void MainWindow::updateFileLabel(QLabel *label, const QString &filePath, const QString &prefix)
{
    if (filePath.isEmpty()) {
        label->setText(prefix + " 未选择");
        label->setStyleSheet("color: black;");
    } else {
        label->setText(prefix + " " + QFileInfo(filePath).fileName());
        label->setStyleSheet("color: green;");
    }
}

void MainWindow::selectGaitVideo()
{
    gaitVideoPath = QFileDialog::getOpenFileName(this, "选择步态视频文件", "", "视频文件 (*.mp4 *.avi)");
    updateFileLabel(gaitVideoLabel, gaitVideoPath, "步态视频:");
}

void MainWindow::selectFaceVideo()
{
    faceVideoPath = QFileDialog::getOpenFileName(this, "选择面部视频文件", "", "视频文件 (*.mp4 *.avi)");
    updateFileLabel(faceVideoLabel, faceVideoPath, "面部视频:");
}

void MainWindow::selectAudio()
{
    audioPath = QFileDialog::getOpenFileName(this, "选择语音文件", "", "音频文件 (*.wav *.mp3)");
    updateFileLabel(audioLabel, audioPath, "语音文件:");
}

void MainWindow::processData()
{
    if (gaitVideoPath.isEmpty() || faceVideoPath.isEmpty() || audioPath.isEmpty()) {
        QMessageBox::warning(this, "文件不完整", "请确保已选择步态视频、面部视频和语音文件。");
        return;
    }

    processDataButton->setEnabled(false);
    generateReportButton->setEnabled(false);
    statusBar()->showMessage("正在上传并处理数据，请稍候...");

    //下面的代码是上传到云端的api接口

    QUrl apiUrl("https://your-cloud-api-endpoint.com/analyze");
    QNetworkRequest request(apiUrl);

    QHttpMultiPart *multiPart = new QHttpMultiPart(QHttpMultiPart::FormDataType);

    QHttpPart gaitVideoPart;
    gaitVideoPart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"gait_video\"; filename=\"" + QFileInfo(gaitVideoPath).fileName() + "\""));
    QFile *gaitFile = new QFile(gaitVideoPath);
    gaitFile->open(QIODevice::ReadOnly);
    gaitVideoPart.setBodyDevice(gaitFile);
    gaitFile->setParent(multiPart);

    QHttpPart faceVideoPart;
    faceVideoPart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"face_video\"; filename=\"" + QFileInfo(faceVideoPath).fileName() + "\""));
    QFile *faceFile = new QFile(faceVideoPath);
    faceFile->open(QIODevice::ReadOnly);
    faceVideoPart.setBodyDevice(faceFile);
    faceFile->setParent(multiPart);

    QHttpPart audioPart;
    audioPart.setHeader(QNetworkRequest::ContentDispositionHeader, QVariant("form-data; name=\"audio_file\"; filename=\"" + QFileInfo(audioPath).fileName() + "\""));
    QFile *audioFile = new QFile(audioPath);
    audioFile->open(QIODevice::ReadOnly);
    audioPart.setBodyDevice(audioFile);
    audioFile->setParent(multiPart);

    multiPart->append(gaitVideoPart);
    multiPart->append(faceVideoPart);
    multiPart->append(audioPart);

    QNetworkReply *reply = networkManager->post(request, multiPart);
    multiPart->setParent(reply); // reply会管理multiPart的生命周期
}

void MainWindow::onAnalysisFinished(QNetworkReply *reply)
{
    processDataButton->setEnabled(true);
    statusBar()->clearMessage();

    if (reply->error() != QNetworkReply::NoError) {
        QMessageBox::critical(this, "网络错误", "请求失败: " + reply->errorString());
        reply->deleteLater();
        return;
    }

    QByteArray responseData = reply->readAll();
    QJsonDocument doc = QJsonDocument::fromJson(responseData);

    if (doc.isObject()) {
        analysisResult = doc.object();
        QString status = analysisResult["status"].toString();
        if (status == "success") {
            QMessageBox::information(this, "处理成功", "数据处理完成，请点击“生成报告”查看结果。");
            generateReportButton->setEnabled(true);
        } else {
            QString message = analysisResult.contains("message") ? analysisResult["message"].toString() : "未知的服务器错误。";
            QMessageBox::critical(this, "处理失败", "服务器返回错误: " + message);
        }
    } else {
        QMessageBox::critical(this, "响应错误", "无法解析服务器返回的数据。");
    }

    reply->deleteLater(); // 释放资源
}

void MainWindow::generateReport()
{
    if (analysisResult.isEmpty()) {
        QMessageBox::warning(this, "无报告", "没有可用的分析结果。");
        return;
    }

    QString prediction = analysisResult["prediction"].toString("未知");
    double confidence = analysisResult["confidence"].toDouble(0.0) * 100.0;

    QString reportText = QString("--- 诊断分析报告 ---\n\n"
                                 "诊断结果: %1\n"
                                 "置信度: %2%\n\n"
                                 "----------------------")
                             .arg(prediction)
                             .arg(confidence, 0, 'f', 2);

    QMessageBox::information(this, "分析报告", reportText);
}

void MainWindow::showPastReports()
{
    QMessageBox::information(this, "功能提示", "“往期报告”功能正在开发中，敬请期待！");
}
