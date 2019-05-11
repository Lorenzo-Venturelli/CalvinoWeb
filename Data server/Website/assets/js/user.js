var ws = WebSocket("wss://tggstudio.eu:8888/ws");

function RTsetSensor(){
    var sensorNumber = document.getElementById("RTSN");
    var value = sensorNumber.options[sensorNumber.selectedIndex].text;

    /* Interfaccia WebSocket richiesta */
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

ws.addEventListener("message", function (message){
    RTupdate(message["temp"], message["light"], message["pressure"], message["highness"]);
});
