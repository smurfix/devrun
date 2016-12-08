	$(document).ready(function(){
		var ws;
		var has_error = false;
		announce = function(c,m) {
			$("div#info").remove();
			if (c == "error") {
				has_error = true;
			}
			var li = $('<div class="alert alert-'+c+'">');
			li.text(c);
			$('div#info').prepend(li);
			$('#page').scrollTop(0);
		}
		//$('form#sender').submit(function(event){
		//	ws.send(JSON.stringify({"type":["note"],"data": $('input#data').val() }));
		//	$('textarea#data').val("");
		//	return false;
		//});
		if ("WebSocket" in window && "devrun" in window && "host" in window.devrun) {
			announce("info","Die Verbindung wird geöffnet …")
			var ws = new WebSocket("ws://" + window.devrun.host +"/api/laden");
			var backlogging = true;

			ws.onmessage = function (msg) {
				var m = $.parseJSON(msg.data);
				if (!('action' in m)) {
				} else if (m.action == 'update' && m.class == 'charger') {
					var f = $('#charger_'+m.name);
					f.find('.f1').text(m.state);
					if (m.charging || m.connected) {
					    f.find('.f2').text(m.amp_avail.toFixed(2));
					} else {
						f.find('.f2').text('–');
					}
					if (m.charging) {
					    f.find('.f3').text(m.amp.toFixed(2));
					    f.find('.f4').text(m.power.toFixed(2));
					    f.find('.f5').text(m.power_factor.toFixed(2));
					} else {
						f.find('.f3').text('–');
						f.find('.f4').text('–');
						f.find('.f5').text('–');
					}
					f.find('.f6').text(m.charge_Wh.toFixed(2));
					f.find('.f7').text((m.charge_sec/60).toFixed(2));
				}
			};
			ws.onopen = function (msg) {
			};
			ws.onerror = function (msg) {
				announce("error","Verbindungsfehler! Bitte laden Sie diese Seite neu.");
			};
			ws.onclose = function (msg) {
				if (has_error) { return; }
				announce("error","Verbindung geschlossen! Bitte laden Sie diese Seite neu.");
			};
		} else if ("WebSocket" in window) {
			announce("error","Interner Fehler! Probieren Sie es später noch einmal.");
		} else {
			announce("error","Sie brauchen einen Browser, der WebSockets unterstützt. Sorry");
		}


		// $.idleTimer(300000); // Hochscrollen nach 5min
		// $(document).bind("idle.idleTimer", function(){
			// $('#page').scrollTop(0);
		// });

	});
