import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import *
import yfinance as yf
import numpy as np
import torch
import matplotlib.pyplot as plt


# Classe que controla habilitação dos botões de ações
class ControlButtonEnability():
    def __init__(self, widgetText, widgetButton ):
        self.textbox = widgetText
        self.button = widgetButton

    def checkStatus(self):
        if self.textbox.text() == "":
            self.textbox.setFocus()
            self.button.setDisabled(True)
        else:
            self.button.setEnabled(True)
            
# Classe do modelo da Rede Neural
class Net(torch.nn.Module):
    def __init__(self, inputSize, hiddenSize):
        super(Net, self).__init__()
        self.inputSize = inputSize
        self.hiddenSize = hiddenSize
        self.fc1 = torch.nn.Linear(self.inputSize, self.hiddenSize)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(self.hiddenSize, 1)
    def forward(self, x):
        hidden = self.fc1(x)
        relu = self.relu(hidden)
        output = self.fc2(relu)
        output = self.relu(output)
        return output



class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setWindowTitle("Análise Temporais - IFTM")
        self.icon = self.setWindowIcon(QIcon("images/icon/icon.png"))
        self.setGeometry(250, 150, 1020, 400)
        self.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint | QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowMinimizeButtonHint)
        self.initUI()
        self.show()
       
    def initUI(self):
        self.criarWidgets()
        self.gerarLayouts()

    '''Cria os widgets que encorporam o Menu e widgets que executaram ações'''
    def criarWidgets(self):
        self.currentDate = QDate.currentDate()
        self.lastDay = self.currentDate.addDays(-1)

        # Widgets do formulário da ação da bolsa de valores
        self.stockTicket = QLineEdit()
        self.stockTicket.setFixedWidth(120)
        
        self.companyName = QLineEdit('')
        self.companyName.setReadOnly(True)
        self.companyName.setFixedWidth(120)
        self.companyName.setStyleSheet("border: 0px; background-color: transparent")

        self.companySection = QLineEdit('')
        self.companySection.setReadOnly(True)
        self.companySection.setFixedWidth(120)
        self.companySection.setStyleSheet("border: 0px; background-color: transparent")

        self.companyCountry = QLineEdit('')
        self.companyCountry.setReadOnly(True)
        self.companyCountry.setFixedWidth(120)
        self.companyCountry.setStyleSheet("border: 0px; background-color: transparent")

        self.currency = QLineEdit('')
        self.currency.setReadOnly(True)
        self.currency.setFixedWidth(120)
        self.currency.setStyleSheet("border: 0px; background-color: transparent")

        self.buttonSearch = QPushButton(self)
        self.buttonSearch.setMaximumWidth(100)
        self.buttonSearch.setText("Procurar") 
        self.buttonSearch.clicked.connect(self.searchStockData)
        self.buttonSearch.setDisabled(True)
        self.controlButtonSearchEnability = ControlButtonEnability(self.stockTicket, self.buttonSearch)
        self.stockTicket.textChanged.connect(self.controlButtonSearchEnability.checkStatus)
        
        
   # Widgets do formulário da série Temporal
        self.epoch = QSpinBox()
        self.epoch.setRange(0,1000000)
        self.epoch.setSingleStep(100)
        self.epoch.setFixedWidth(90)
        self.epoch.setValue(15000)
        
        self.totalHiddenLayers = QSpinBox()
        self.totalHiddenLayers.setRange(0,1000)
        self.totalHiddenLayers.setSingleStep(1)
        self.totalHiddenLayers.setFixedWidth(90)
        self.totalHiddenLayers.setValue(100)

        self.learningRate = QDoubleSpinBox ()
        self.learningRate.setSingleStep(0.1)
        self.learningRate.setFixedWidth(90)
        self.learningRate.setValue(0.09)

        self.momentumValue = QDoubleSpinBox ()
        self.momentumValue.setSingleStep(0.1)
        self.momentumValue.setFixedWidth(90)
        self.momentumValue.setValue(0.03)

        self.inicialDate = QDateEdit(calendarPopup=True)
        self.inicialDate.setDate(self.lastDay)
        self.inicialDate.setMaximumDate(self.lastDay)
        self.inicialDate.setFixedWidth(90)

        self.finalDate = QDateEdit(calendarPopup=True)
        self.finalDate.setDate(self.currentDate)
        self.finalDate.setMaximumDate(self.currentDate)
        self.finalDate.setFixedWidth(90)

        self.buttonSubmit = QPushButton(self)
        self.buttonSubmit.setMaximumWidth(100)
        self.buttonSubmit.setText("Submeter") 
        self.buttonSubmit.clicked.connect(self.handleTemporalAnalysis)
        self.buttonSubmit.setDisabled(True)

        self.controlButtonSubmitEnability = ControlButtonEnability(self.companyName, self.buttonSubmit)
        self.companyName.textChanged.connect(self.controlButtonSubmitEnability.checkStatus)
        
        # Widgets dos gráficos
        self.bottom = QFrame()
        self.bottom.setFrameShape(QFrame.StyledPanel)

        self.image = QLabel()
        self.dirImage = QtGui.QPixmap('images/imagemPadrao.png')
        self.image.setPixmap(self.dirImage)
        self.image.setAlignment(QtCore.Qt.AlignCenter)

        self.buttonClean = QPushButton(self)
        self.buttonClean.setMaximumWidth(100)
        self.buttonClean.setText("Limpar") 
        self.buttonClean.clicked.connect(self.setDefaultImage)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.image)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.splitter)       
        
        # Grupo com os elementos que exibirão os dados da ação da bolsa de valores
        self.stockGroupBox = QGroupBox("Dados da Ação da Bolsa de Valores")
        layout = QFormLayout()
        layout.addRow(QLabel("Informe o símbolo da Ação:"), self.stockTicket)
        layout.addRow(QLabel("Nome da empresa:"), self.companyName)
        layout.addRow(QLabel("Setor:"), self.companySection)
        layout.addRow(QLabel("País:"), self.companyCountry)
        layout.addRow(QLabel("Moeda:"), self.currency)
        layout.addWidget(self.buttonSearch)
        layout.setVerticalSpacing(10)
        self.stockGroupBox.setLayout(layout)

        # Grupo com os elementos exibirão os valores para a análise temporal
        self.temporalAnalysisGroupBox = QGroupBox("Dados Série Temporal")
        layout = QFormLayout()
        layout.addRow(QLabel("Número de épocas de treinamento:"), self.epoch)
        layout.addRow(QLabel("Número de neurônios na camada oculta:"), self.totalHiddenLayers)
        layout.addRow(QLabel("Valor Learning Rate:"), self.learningRate)
        layout.addRow(QLabel("Valor Momentum:"), self.momentumValue)
        layout.addRow(QLabel("Data Inicial:"), self.inicialDate)
        layout.addRow(QLabel("Data Final:"), self.finalDate)
        layout.addWidget(self.buttonSubmit)
        layout.setVerticalSpacing(10)
        self.temporalAnalysisGroupBox.setLayout(layout)    
        
        '''Gerar Layouts'''
    def gerarLayouts(self):
        # Criando janela
        self.janelaAreaVisualizacao = QWidget(self)
        self.setCentralWidget(self.janelaAreaVisualizacao)     

        # Criando os layouts
        self.mainLayout = QHBoxLayout()
        self.leftLayout = QVBoxLayout()
        self.rightLayout = QHBoxLayout()

        # Adicionando os widgets
        self.leftLayout.addWidget(self.stockGroupBox)
        self.leftLayout.addWidget(self.temporalAnalysisGroupBox)
        self.rightLayout.addWidget(self.scrollArea)
        self.rightLayout.addWidget(self.buttonClean)

        # Adicionando layouts filhos na janela principal
        self.mainLayout.addLayout(self.leftLayout, 2)
        self.mainLayout.addLayout(self.rightLayout, 20)

        self.janelaAreaVisualizacao.setLayout(self.mainLayout)

    def setDefaultImage(self):
        self.image.setPixmap(self.dirImage)
        self.image.setAlignment(QtCore.Qt.AlignCenter)

        
    def searchStockData(self):
        self.stockSelected = self.stockTicket.text().upper()
        self.stockData = yf.Ticker(self.stockSelected)
        if (len(self.stockData.actions) > 0) :
            self.companyName.setText(self.stockData.info['longName'])
            self.companySection.setText(self.stockData.info['sector'])
            self.companyCountry.setText(self.stockData.info['country'])
            self.currency.setText(self.stockData.info['currency'])
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Erro")
            msg.setInformativeText('Ação não encontrada!')
            msg.setWindowTitle("Erro")
            msg.exec_()
            self.stockTicket.setFocus()

    def handleTemporalAnalysis(self):

        startDate = self.inicialDate.date().toString(Qt.ISODate)
        endDate = self.finalDate.date().toString(Qt.ISODate)
        data = yf.download(self.stockSelected, start=startDate, end=endDate)
        data = data.Close
        if (data.size < 910):
            msg = QMessageBox()
            msg.setStyleSheet("width: 120px;")
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Erro")
            msg.setText("Erro - Dados insuficientes")
            msg.setInformativeText("Total base de dados:  " +  str(data.size))
            descricao = "Para realizar a análise e predição é necessário ter uma base de dados de no mínimo 910 valores de fechamento diário. \
                \n\nPara que prosseguir modifique o período entre a data inicial e final selecionados" 
            msg.setDetailedText(descricao)
            msg.exec_()
            self.inicialDate.setFocus()
        else: 
            # Criar janela deslizante
            windowing = 50        
            finalData = np.zeros([abs(data.size - windowing), windowing + 1])
            for i in range(len(finalData)):
                for j in range(windowing + 1):
                    finalData[i][j] = data.iloc[i+j]
        
            # Normalizar entre 0 e 1
            max = finalData.max()
            min = finalData.min()
            dif = max - min
            finalData = (finalData - finalData.min())/dif
            x = finalData[:, :-1]
            y = finalData[:, -1]

            # Converter para tensor
            # Entrada do treinamento
            # Saída do treinamento
            trainingInput = torch.FloatTensor(x[:850, :])
            trainingOutput = torch.FloatTensor(y[:850])
            testOutput = torch.FloatTensor(y[850:])

            # #Entrada do teste
            # #Saída do teste
            testInput = torch.FloatTensor(x[850: , :])

            # Criar a instância do modelo
            inputSize = trainingInput.size()[1]
            hiddenSize = self.totalHiddenLayers.value()
            model = Net(inputSize, hiddenSize)

            # Critério de erro
            criterion = torch.nn.MSELoss()

            # Criando os paramêtros (learning rate[obrigatória] e momentum[opcional])
            lr = self.learningRate.value()
            momentum = self.momentumValue.value()
            optimizer = torch.optim.SGD(model.parameters(), lr, momentum)
            
            # Treinamento
            model.train()
            epochs = self.epoch.value()
            errors = []
            for epoch in range(epochs):
                optimizer.zero_grad()
                # Fazer o forward
                yPred = model(trainingInput)
                # Cálculo do erro
                loss = criterion(yPred.squeeze(), trainingOutput)
                errors.append(loss.item())
                # Backpropagation
                loss.backward()
                optimizer.step()

            # Testar o modelo já treinado
            model.eval()
            yPred = model(testInput)
            afterTrain = criterion(yPred.squeeze(), testOutput)
            self.plotcharts(errors, testOutput, yPred)


    
    def plotcharts(self, errors, testOutput, yPred):

        errors = np.array(errors)
        lasterrors = np.array(errors[-25000:])
        plt.figure(figsize=(18, 4))
        graf01 = plt.subplot(1, 3, 1) # nrows, ncols, index
        graf01.set_title('Evolução dos Erros')
        plt.plot(errors, '-')
        plt.xlabel('Épocas')
        graf02 = plt.subplot(1, 3, 2) # nrows, ncols, index
        graf02.set_title('Últimos 25.000 erros')
        plt.plot(lasterrors, '-')
        plt.xlabel('Épocas')
        graf03 = plt.subplot(1, 3, 3)
        graf03.set_title('Resultado Predição')
        a = plt.plot(testOutput.numpy(), 'y-', label='Real')
        a = plt.plot(yPred.detach().numpy(), 'b-', label='Predicted')
        plt.legend(loc=7)
        newImage = "graficosResultado.png"
        plt.savefig('./images/' + newImage, format="png")
        newDirImageValuePerDay = QtGui.QPixmap('./images/' + newImage)
        self.image.setPixmap(newDirImageValuePerDay)


def main():
    app = QApplication(sys.argv)
    win = MyWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
    
    
