var ws = new WebSocket("wss://tggstudio.eu/ws");

var currentRTSN = document.getElementById("RTSN");
currentRTSN = currentRTSN.options[currentRTSN.selectedIndex].text;
var pingInterval = null
var remoteServerStatus = true

const graph = {
    chart : null,
    lowerYvalue : 0,
    graphData : {},
    graphXlabels : [],
    firstTime : null,
    lastTime : null,
    updateReason : [],

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
                            beginAtZero: false,
                            min : 0
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
    },

    addNewSensor(self, sensorNumber){
        console.log(sensorNumber)
        if(sensorNumber in self.graphData){
            return false;
        }
        else{
            self.graphData[sensorNumber] = {};
            return true;
        }
    },

    addNewDataType(self, sensorNumber, dataType){
        if(sensorNumber in self.graphData){
            if(dataType in self.graphData){
                return false;
            }
            else{
                self.graphData[sensorNumber][dataType] = null;
                return true;
            }
        }
        else{
            if(self.addNewSensor(sensorNumber) == true){
                self.graphData[sensorNumber][dataType] = null;
                return true;
            }
            else{
                return false;
            }
        }
    },

    addNewValues(self, sensorNumber, dataType, value){
        if(sensorNumber in self.graphData){
            if(dataType in self.graphData[sensorNumber]){
                self.graphData[sensorNumber][dataType] = value;
                return true;
            }
            else{
                if(self.addNewDataType(sensorNumber, dataType) == true){
                    self.graphData[sensorNumber][dataType] = value;
                    return true;
                }
                else{
                    return false;
                }
            }
        }
        else{
            if(self.addNewSensor(sensorNumber) == true){
                if(self.addNewDataType(sensorNumber, dataType) == true){
                    self.graphData[sensorNumber][dataType] = value;
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
    },

    removeSensor(self, sensorNumber){
        if(sensorNumber in self.graphData){
            delete self.graphData[sensorNumber];
            return true;
        }
        else{
            return false;
        }
    },

    removeDataType(self, sensorNumber, dataType){
        if(sensorNumber in self.graphData){
            if(dataType in self.graphData){
                delete self.graphData[sensorNumber][dataType];
                return true;
            }
            else{
                return false;
            }
        }
        else{
            return false;
        }
    },

    clearGraph(self){
        self.lowerYvalue = 0;
        self.graphData = {};
        self.graphXlabels = [];
        self.firstTime = null;
        self.lastTime = null;
        return;
    },

    generateNewGraph(self, sensorNumber, dataType, value){
        this.clearGraph(self);

        if(this.addNewSensor(self, sensorNumber) == false){
            return false;
        }
        if(this.addNewDataType(self, sensorNumber, dataType) == false){
            return false;
        }
        var tmp = [];
        for(xVal in value){
            self.graphXlabels.push(xVal);
            tmp.push(value[xVal]);
        }
        if(this.addNewValues(self, sensorNumber, dataType, tmp) == false){
            return false;
        }

        self.firstTime = self.graphXlabels[0];
        self.lastTime = self.graphXlabels[self.graphXlabels.length - 1];
        console.log(self)

        self.lowerYvalue = Math.round((Math.min(...self.graphData[sensorNumber][dataType]) - (Math.max(...self.graphData[sensorNumber][dataType])) / 4));
        var dataset = {
            label : [String(dataType + " " + sensorNumber)],
            data : self.graphData[sensorNumber][dataType],
            backgroundColor : ['rgba(255, 99, 132, 0.2)']
        }

        self.chart.data.labels = self.graphXlabels
        self.chart.data.datasets = []
        self.chart.data.datasets.push(dataset);
        self.chart.options.scales.yAxes[0].ticks.min = self.lowerYvalue;
        self.chart.update()

        return true;
    }
};

var chart = Object.create(graph);

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
    if(reason == 1){
        graph.updateReason.push(1);
        GDrequest();
        return;
    }
    else if(reason == 2){
        graph.updateReason.push(1);
        return;
    }
    else if(reason == 3){
        graph.updateReason.push(1);
        return;
    }
    else{
        return;
    }
}

function GDrequest(){
    if(remoteServerStatus == true){
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
    
        sendGDrequest(sensorNumber, dataType, firstTime, lastTime);
    }
    else{
        alert("Il server MQTT non è disponibile al momento");
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
    graph.generateNewGraph(chart, sensorNumber, dataType, graphData);
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
        var reason = graph.updateReason.pop();
        if (reason == 1){
            buildGraph(receivedData["values"], receivedData["dataType"], receivedData["sensorNumber"]);
        }
        
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
