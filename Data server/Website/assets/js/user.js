var ws = new WebSocket("wss://tggstudio.eu/ws");

var currentRTSN = document.getElementById("RTSN");
currentRTSN = currentRTSN.options[currentRTSN.selectedIndex].text;
var pingInterval = null
var remoteServerStatus = true

class Graph{
    constructor(){
        this.chart = null;
        this.lowerYvalue = 0;
        this.graphData = {};
        this.graphXlabels = [];
        this.firstTime = null;
        this.lastTime = null;
        this.updateReason = [];
        this.type = null;
        this.initializated = false;
    }

    initializeGraph(graphElementID){
        var ctx = document.getElementById(graphElementID).getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels : [],
                datasets : []
            },
            options: {
                scales: {
                    yAxes: [{
                        gridLines: {
                            color: "#ecf0f1"
                        },
                        ticks: {
                            fontColor: "#636363",
                            beginAtZero: true,
                            //min : 0
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            color: "#ecf0f1",
                            fontColor: "#636363"
                        }
                    }]
                }
            }
        });
        return;
    }

    addNewSensor(sensorNumber){
        console.log(sensorNumber)
        if(sensorNumber in this.graphData){
            return false;
        }
        else{
            this.graphData[sensorNumber] = {};
            return true;
        }
    }

    addNewDataType(sensorNumber, dataType){
        if(sensorNumber in this.graphData){
            if(dataType in this.graphData){
                return false;
            }
            else{
                this.graphData[sensorNumber][dataType] = null;
                return true;
            }
        }
        else{
            if(this.addNewSensor(sensorNumber) == true){
                this.graphData[sensorNumber][dataType] = null;
                return true;
            }
            else{
                return false;
            }
        }
    }

    addNewValues(sensorNumber, dataType, value){
        if(sensorNumber in this.graphData){
            if(dataType in this.graphData[sensorNumber]){
                this.graphData[sensorNumber][dataType] = value;
                return true;
            }
            else{
                if(this.addNewDataType(sensorNumber, dataType) == true){
                    this.graphData[sensorNumber][dataType] = value;
                    return true;
                }
                else{
                    return false;
                }
            }
        }
        else{
            if(this.addNewSensor(sensorNumber) == true){
                if(this.addNewDataType(sensorNumber, dataType) == true){
                    this.graphData[sensorNumber][dataType] = value;
                    return true;
                }
                else{
                    return false;
                }
            }
            else{
                return false;
            }
        }
    }

    removeSensor(sensorNumber){
        if(sensorNumber in this.graphData){
            delete this.graphData[sensorNumber];
            return true;
        }
        else{
            return false;
        }
    }

    removeDataType(sensorNumber, dataType){
        if(sensorNumber in this.graphData){
            if(dataType in this.graphData){
                delete this.graphData[sensorNumber][dataType];
                return true;
            }
            else{
                return false;
            }
        }
        else{
            return false;
        }
    }

    clearGraph(){
        this.lowerYvalue = 0;
        this.graphData = {};
        this.graphXlabels = [];
        this.firstTime = null;
        this.lastTime = null;
        this.type = null;
        return;
    }

    generateNewGraph(sensorNumber, dataType, value){
        this.clearGraph();
        this.type = dataType;

        if(this.addNewSensor(sensorNumber) == false){
            return false;
        }
        if(this.addNewDataType(sensorNumber, dataType) == false){
            return false;
        }
        var tmp = [];
        for(var xVal in value){
            this.graphXlabels.push(xVal);
            tmp.push(value[xVal]);
        }
        if(this.addNewValues(sensorNumber, dataType, tmp) == false){
            return false;
        }

        this.firstTime = this.graphXlabels[0];
        this.lastTime = this.graphXlabels[this.graphXlabels.length - 1];

        var dataset = {
            label : String(dataType + " " + sensorNumber),
            data : this.graphData[sensorNumber][dataType],
            backgroundColor : 'rgba(' + (Math.floor(Math.random() * 256)) + ', ' + (Math.floor(Math.random() * 256)) + ', ' + (Math.floor(Math.random() * 256)) +  ', 0.2)'
        }

        this.chart.data.labels = this.graphXlabels;
        this.chart.data.datasets = [];
        this.chart.data.datasets.push(dataset);
        this.chart.update();
        this.initializated = true;

        return true;
    }

    addElement(sensorNumber, dataType, value){
        if(this.initializated == true){
            if(this.type != dataType){
                return false;
            }
    
            if(this.addNewSensor(sensorNumber) == false){
                return false;
            }
            if(this.addNewDataType(sensorNumber, dataType) == false){
                return false;
            }
            var tmp = [];
            for(var xVal in value){
                tmp.push(value[xVal]);
            }
            if(this.addNewValues(sensorNumber, dataType, tmp) == false){
                return false;
            }
    
            var dataset = {
                label : String(dataType + " " + sensorNumber),
                data : this.graphData[sensorNumber][dataType],
                backgroundColor : 'rgba(' + (Math.floor(Math.random() * 256)) + ',' + (Math.floor(Math.random() * 256)) + ',' + (Math.floor(Math.random() * 256)) +  ', 0.2)'
            }
    
            this.chart.data.datasets.push(dataset);
            this.chart.options.scales.yAxes[0].ticks.min = this.lowerYvalue;
            this.chart.update()
        }
        else{
            return false;
        }
    }

    removeElement(sensorNumber, dataType){
        if(this.initializated == true && this.chart.data.datasets.length > 1){
            this.removeDataType(sensorNumber, dataType);
            this.removeSensor(sensorNumber);
            var dataset = null;
            var searchedDataset = String(dataType + " " + sensorNumber)
            console.log(searchedDataset)
            for(dataset in this.chart.data.datasets){
                if (this.chart.data.datasets[dataset].label == searchedDataset){
                    this.chart.data.datasets.splice(dataset, 1);
                    this.chart.update();
                }
            }
        }
    }

    checkElement(sensorNumber, dataType){
        if(sensorNumber in this.graphData){
            if(dataType in this.graphData[sensorNumber]){
                return true;
            }
        }

        return false;
    }
}

var chart = new Graph();

function setDefault(){
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();

    document.getElementById("GFTD").defaultValue = yyyy + "-" + mm + "-" + dd;
    document.getElementById("GLTD").defaultValue = yyyy + "-" + mm + "-" + dd;
    document.getElementById("GFTT").defaultValue = "00:00";
    document.getElementById("GLTT").defaultValue = "01:00";

    chart.initializeGraph("graph");


    pingInterval = setInterval(pingServer, 5000);
}

function RTsetSensor(){
    if (remoteServerStatus == true){
        var sensorNumber = document.getElementById("RTSN");
        var value = sensorNumber.options[sensorNumber.selectedIndex].text;
        if (value != currentRTSN){
            currentRTSN = value;
            sendRTupdate(value);
        }
    }
    else{
        alert("Il server MQTT non è disponibile al momento");
    }


    return;
}

function RTupdate(temp, light, pressure, highness){
    document.getElementById("rtTemp").innerText = temp;
    document.getElementById("rtLight").innerText = light;
    document.getElementById("rtPressure").innerText = pressure;
    document.getElementById("rtHighness").innerText = highness;
    return;
}

function changeGraph(reason){
    while(chart.updateReason.length > 1){}
    if(reason == 1){
        chart.updateReason.push(1);
        GDrequest();
        return;
    }
    else if(reason == 2){
        chart.updateReason.push(2);
        GDrequest();
        return;
    }
    else if(reason == 3){
        chart.updateReason.push(3);
        GDrequest();
        return;
    }
    else{
        return;
    }
}

function GDrequest(){
    if(remoteServerStatus == true){
        var currentTime = new Date()
        if(chart.updateReason[0] == 1){
            var x = document.getElementById("GSN");
            var sensorNumber = x.options[x.selectedIndex].value;
            x = document.getElementById("GDT");
            var dataType = x.options[x.selectedIndex].value;
            var Fdata = document.getElementById("GFTD").value;
            var Ldata = document.getElementById("GLTD").value;
            var Ftime = document.getElementById("GFTT").value;
            var Ltime = document.getElementById("GLTT").value;
        
            var firstTime = Fdata + " " + Ftime + ":00";
            var lastTime = Ldata + " " + Ltime + ":00";

            if(Date.parse(lastTime) > Date.parse(firstTime)){
                if(Date.parse(lastTime) < currentTime){
                    sendGDrequest(sensorNumber, dataType, firstTime, lastTime);
                }
                else{
                    window.alert("La data di fine deve essere antecedente alla data attuale!")
                    chart.updateReason.pop()
                }
                
            }
            else{
                window.alert("La data di inizio deve essere antecedente a quella di fine!")
                chart.updateReason.pop()
            }  
        }
        else if(chart.updateReason[0] == 2 && chart.initializated == true){
            var x = document.getElementById("GSN");
            var sensorNumber = x.options[x.selectedIndex].value;
            x = document.getElementById("GDT");
            var dataType = x.options[x.selectedIndex].value;
            var firstTime = chart.firstTime;
            var lastTime = chart.lastTime;

            if(chart.checkElement(sensorNumber, dataType) == false){
                sendGDrequest(sensorNumber, dataType, firstTime, lastTime);
            }
            else{
                chart.updateReason.pop()
            }
        }
        else if (chart.updateReason[0] == 3 && chart.initializated == true){
            var x = document.getElementById("GSN");
            var sensorNumber = x.options[x.selectedIndex].value;
            x = document.getElementById("GDT");
            var dataType = x.options[x.selectedIndex].value;
            chart.updateReason.pop();
            chart.removeElement(sensorNumber, dataType);
        }
        else{
            chart.updateReason.pop()
        }
    }
    else{
        alert("Il server MQTT non è disponibile al momento");
        chart.updateReason.pop()
    }

    return;
}

function sendRTupdate(sensorNumber){
    var message = {"realTimeSN" : sensorNumber};
    message = JSON.stringify(message)
    ws.send(message);
    return;
}

function sendGDrequest(sensorNumber, dataType, firstTime, lastTime){
    var message = {"grapRequest" : {"SN" : sensorNumber, "DT" : dataType, "FT" : firstTime, "LT" : lastTime}};
    message = JSON.stringify(message)
    ws.send(message);
    return;
}

function pingServer(){
    ws.send("ping");
    return;
}

function buildGraph(graphData, dataType, sensorNumber){
    if(chart.updateReason[0] == 1){
        chart.updateReason.pop();
        chart.generateNewGraph(sensorNumber, dataType, graphData);
    }
    else if(chart.updateReason[0] == 2){
        chart.updateReason.pop();
        chart.addElement(sensorNumber, dataType, graphData);
    }
    else{
        chart.updateReason.pop();
    }
    
    return;
}

ws.addEventListener("message", function (message){
    var receivedData = JSON.parse(message.data);

    if (receivedData["type"] == "rtd"){
        if(remoteServerStatus == true){
            RTupdate(receivedData["temp"], receivedData["light"], receivedData["pressure"], receivedData["highness"]);
        }
        else{
            RTupdate("0", "0", "0", "0");
        }
    }
    else if (receivedData["type"] == "pong"){
        if (receivedData["status"] == "close"){
            clearInterval(pingInterval);
            ws.close();
        }
    }
    else if (receivedData["type"] == "gr"){
        buildGraph(receivedData["values"], receivedData["dataType"], receivedData["sensorNumber"]);
    }
    else if(receivedData["type"] == "service"){
        if (receivedData["status"] == "down" && remoteServerStatus == true){
            remoteServerStatus = false;
        }
        else if (receivedData["status"] == "up" && remoteServerStatus == false){
            remoteServerStatus = true;
        }
    }

});

ws.addEventListener("close", function(){
    console.log("OK")
});
