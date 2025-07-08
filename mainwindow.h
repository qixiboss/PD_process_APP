// MainWindow.h

#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QNetworkAccessManager>
#include <QJsonObject>

// 前向声明
class QLabel;
class QPushButton;
class QNetworkReply;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    // 文件选择槽
    void selectGaitVideo();
    void selectFaceVideo();
    void selectAudio();

    // 控制按钮槽
    void processData();
    void generateReport();
    void showPastReports();

    // 网络请求完成后的处理槽
    void onAnalysisFinished(QNetworkReply *reply);

private:
    void setupUi();
    void updateFileLabel(QLabel *label, const QString &filePath, const QString &prefix);

    // UI 组件
    QLabel *gaitVideoLabel;
    QLabel *faceVideoLabel;
    QLabel *audioLabel;
    QPushButton *gaitVideoButton;
    QPushButton *faceVideoButton;
    QPushButton *audioButton;
    QPushButton *processDataButton;
    QPushButton *generateReportButton;
    QPushButton *pastReportsButton;

    // 数据存储
    QString gaitVideoPath;
    QString faceVideoPath;
    QString audioPath;
    QJsonObject analysisResult; // 存储从API返回的JSON结果

    // 网络相关
    QNetworkAccessManager *networkManager;
};

#endif // MAINWINDOW_H
