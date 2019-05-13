var ws = WebSocket("wss://tggstudio.eu:8888/ws");
var ctx = document.getElementById('graph').getContext('2d');

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
}

function RTsetSensor(){
    var sensorNumber = document.getElementById("RTSN");
    var value = sensorNumber.options[sensorNumber.selectedIndex].text;
    sendRTupdate(value);
    return
}

function RTupdate(temp, light, pressure, highness){
    var element = document.getElementById("rtTemp");
    element.nodeValue = temp;
    element = document.getElementById("rtLight");
    element.nodeValue = light;
    element = document.getElementById("rtPressure");
    element.nodeValue = pressure;
    element = document.getElementById("rtHighness");
    element.nodeValue = highness
    return;
}

function GDrequest(){
    var x = document.getElementById("GSN");
    var sensorNumber = x.options[x.selectedIndex].text;
    x = document.getElementById("GDT");
    var dataType = x.options[x.selectedIndex].text;
    var Fdata = document.getElementById("GFTD").value
    var Ldata = document.getElementById("GLTD").value
    var Ftime = document.getElementById("GFTT").value
    var Ltime = document.getElementById("GLTT").value

    var firstTime = Fdata + " " + Ftime + ":00"
    var lastTime = Ldata + " " + Ltime + ":00"

    sendGDrequest(sensorNumber, dataType, firstTime, lastTime);
    return;
}

function sendRTupdate(sensorNumber){
    ws.send({"realTimeSN" : sensorNumber});
    return;
}

function sendGDrequest(sensorNumber, dataType, firstTime, lastTime){
    ws.send({"grapRequest" : [{"SN" : sensorNumber, "DT" : dataType, "FT" : firstTime, "LT" : lastTime}]});
    return;
}

function buildGraph(){
    var datas = [20.1, 22, 30, 20, 21, 20.1];
    var dataType = "Temperatura in °C"
    var minValue = Math.min(...datas) - 2;


    var chart = new Chart(ctx, {
        type: 'line',
        data: {
        labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
        datasets: [{
            label: dataType,
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
                    ticks: {
                        beginAtZero: false,
                        min : minValue
                    }
                }]
            }
        }
    });
}

ws.addEventListener("message", function (message){
    if (message["type"] == "RTD"){
        RTupdate(message["temp"], message["light"], message["pressure"], message["highness"]);
    }
    else{
        //
    }
});
