var ws = new WebSocket("wss://tggstudio.eu/ws");
var ctx = document.getElementById('graph').getContext('2d');
var currentRTSN = document.getElementById("RTSN");
currentRTSN = currentRTSN.options[currentRTSN.selectedIndex].text;
var pingInterval = null
var chart = null

function setDefault(){
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();

    document.getElementById("GFTD").defaultValue = yyyy + "-" + mm + "-" + dd;
    document.getElementById("GLTD").defaultValue = yyyy + "-" + mm + "-" + dd;
    document.getElementById("GFTT").defaultValue = "00:00";
    document.getElementById("GLTT").defaultValue = "01:00";

    buildGraph();

    pingInterval = setInterval(pingServer, 5000);
}

function RTsetSensor(){
    var sensorNumber = document.getElementById("RTSN");
    var value = sensorNumber.options[sensorNumber.selectedIndex].text;
    if (value != currentRTSN){
        currentRTSN = value;
        sendRTupdate(value);
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

function GDrequest(){
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

function buildGraph(grapData, dataType, sensorNumber){
    var ctx = document.getElementById('graph').getContext('2d');
    var datas = [];
    var labels = [];
    for(var xVal in grapData){
        datas.push(grapData[xVal]);
        labels.push(xVal);
    }
    var dataLabel = null;
    switch(dataType){
        case "temperatura":{
            dataLabel = "Temperatura in °C";
            break;
        }
        case "luce":{
            dataLabel = "Luce";
            break;
        }
        case "altitudine":{
            dataLabel = "Altitudine";
            break;
        }
        case "pressione":{
            dataLabel = "Pressione";
            break;
        }
    }
    var minValue = Math.min(...datas) - 2;

    chart = new Chart(ctx, {
        type: 'line',
        data: {
        labels: labels,
        datasets: [{
            label: dataLabel,
            data: datas,
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)'
            ],
            borderWidth: 1
        }]
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
                    min : minValue
                }
                }],
                xAxes: [{
                gridLines: {
                    color: "#ecf0f1"
                },
                ticks: {
                    fontColor: "#636363",
                }
                }]
            }
        }
    });
    

}

ws.addEventListener("message", function (message){
    var receivedData = JSON.parse(message.data)
    console.log(receivedData);
    if (receivedData["type"] == "rtd"){
        RTupdate(receivedData["temp"], receivedData["light"], receivedData["pressure"], receivedData["highness"]);
    }
    else if (receivedData["type"] == "pong"){
        if (receivedData["status"] == "close"){
            clearInterval(pingInterval);
            ws.close();
        }
    }
    else if (receivedData["type"] == "gr"){
        console.log(receivedData["values"])
        buildGraph(receivedData["values"], receivedData["dataType"], receivedData["sensorNumbers"]);
    }
});

ws.addEventListener("close", function(){
    console.log("OK")
});
