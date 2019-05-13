var ws = WebSocket("wss://tggstudio.eu:8888/ws");
var ctx = document.getElementById('graph').getContext('2d');
var chart = new Chart(ctx, {
    type: 'line',
});

function setDefault(){
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();

    document.getElementById("GFTD").defaultValue = yyyy + "-" + mm + "-" + dd;
    document.getElementById("GLTD").defaultValue = yyyy + "-" + mm + "-" + dd;
    document.getElementById("GFTT").defaultValue = "00:00";
    document.getElementById("GLTT").defaultValue = "01:00";
}

function RTsetSensor(){
    var sensorNumber = document.getElementById("RTSN");
    var value = sensorNumber.options[sensorNumber.selectedIndex].text;
    console.log(value)
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

function GDrequest(){
    var x = document.getElementById("GSN");
    var sensorNumber = x.options[x.selectedIndex].text;
    x = document.getElementById("GDT");
    var dataType = x.options[x.selectedIndex].text;
    var Fdata = document.getElementById("GFTD").value
    var Ldata = document.getElementById("GLTD").value
    var Ftime = document.getElementById("GFTT").value
    var Ltime = document.getElementById("GLTT").value

    /* Interfaccia WebSocket richiesta */
}

ws.addEventListener("message", function (message){
    if (message["type"] == "RTD"){
        RTupdate(message["temp"], message["light"], message["pressure"], message["highness"]);
    }
    else{
        //
    }
});
