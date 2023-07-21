TABLE_NAME = "x_1067116_astra_co_ac_notifications";
REST_NAME = "x_1067116_astra_co.Astra Control - List Notifications";
EVENTQ_NAME = "x_1067116_astra_co.AstraControlEventNoti";

// Performs a GET API call against the notifications endpoint in Astra Control
function makeApiCall() {
    var r = new sn_ws.RESTMessageV2(REST_NAME, "Default GET");
    r.setStringParameterNoEscape("AstraFQDN", "astra.netapp.io");
    r.setStringParameterNoEscape("AccountID", "12345678-abcd-4efg-1234-567890abcdef");
    r.setStringParameterNoEscape("API_Token", "Bearer thisIsJustAnExample_token-replaceWithYours==");
    var response = r.execute();
    var responseBody = response.getBody();
    return JSON.parse(responseBody);
}

// Finds and returns the largest sequencecount value from the database
function getSequenceCount() {
    var lastSequenceCount = 0;
    var target = new GlideRecord(TABLE_NAME);
    target.query(); 
    while(target.next()) {
        if (Number(target.sequencecount) > lastSequenceCount) {
            lastSequenceCount = Number(target.sequencecount);
        }
    }
    gs.info("last sequencecount in DB: " + lastSequenceCount);
    return lastSequenceCount;
}

// Adds a new notification object to the database
function addToDB(jObject) {
    gs.info("Adding notificationID " + JSON.stringify(jObject.id) + " with sequenceCount " + sequenceCount + " to DB");
    var rinsert = new GlideRecord(TABLE_NAME);
    rinsert.initialize();
    rinsert.setValue("sequencecount", sequenceCount);
    rinsert.setValue("body", JSON.stringify(jObject));
    rinsert.update();
    return rinsert;
}

// Opens an incident based on a notification json
function openIncident(jObject) {
    gs.info("Opening case for notificationID " + jObject.id + " with summary: " + jObject.summary);
    var inc = new GlideRecord("incident");
    inc.initialize();
    inc.short_description = "Astra Control: " + jObject.summary;
    inc.description = jObject.description;
    inc.description += "\n\n" + JSON.stringify(jObject, null, 4);
    inc.impact = 2;
    inc.urgency = 2;
    inc.insert();
}

// Creates an event
function createEvent(jObject, glideRecordObject) {
    gs.info("Creating event for notificationID " + jObject.id + " with summary: " + jObject.summary);
    var summary = "Astra Control: " + jObject.summary;
    var description = JSON.stringify(jObject, null, 4);
    gs.eventQueue(EVENTQ_NAME, glideRecordObject, summary, description);
}

try {
    var lastSequenceCount = getSequenceCount();
    var rjson = makeApiCall();
    // Loop through the notifications response
    for (var i = 0; i < rjson.items.length; i++) {
        var sequenceCount = Number(JSON.stringify(rjson.items[i].sequenceCount));
        // If true, then it's a new notification
        if (sequenceCount > lastSequenceCount) {
            var glideRecordObject = addToDB(rjson.items[i]);
            // Create an event for all notification types
            createEvent(rjson.items[i], glideRecordObject);

            // Optionally uncomment if you prefer to directly open a case
            //var severity = JSON.stringify(rjson.items[i].severity);
            //if (severity.contains("warning") || severity.contains("critical")) {
                //openIncident(rjson.items[i]);
            //}
        }
    }
}
catch(ex) {
    gs.error(ex.message);
}
