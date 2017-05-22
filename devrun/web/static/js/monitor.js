	$(document).ready(function(){
		var ws;
		var has_error = false;
		var num = 0;
		announce = function(c,m) {
			var inf = $("div#info");
			inf.empty();
			// var li = $('<div class="alert alert-'+c+'" />');
			var li = $('<div/>');
			num = num+1;
			var n = num;
			li.attr('id', 'alert-'+n)
			li.addClass('alert');
			li.addClass('alert-'+c);
			li.addClass('fade');
			li.addClass('fade in');
			li.text(m);
			inf.prepend(li);
			$('#page').scrollTop(0);
			if (c != "danger") {
				setTimeout(function(){ 
					$('#alert-'+n).alert('close')
				}, 2000);
			}
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
					    f.find('.f2').text(m.amp_avail.toFixed(1));
					} else {
					    f.find('.f2').text('('+m.amp_avail.toFixed(1)+')');
					}
					if (m.charging) {
					    f.find('.f3').text(m.amp.toFixed(2));
					    f.find('.f4').text((m.power/1000).toFixed(2));
					    f.find('.f5').text(m.power_factor.toFixed(2));
					} else {
						f.find('.f3').text('–');
						f.find('.f4').text('–');
						f.find('.f5').text('–');
					}
					f.find('.f6').text((m.charge_Wh/1000).toFixed(2));
					f.find('.f7').text((m.charge_sec/60).toFixed(1));
				}
			};
			ws.onopen = function (msg) {
			    announce("success","Die Tabelle wird automatisch aktualisiert.");
			};
			ws.onerror = function (msg) {
				announce("danger","Verbindungsfehler! Bitte laden Sie diese Seite ggf. neu.");
			};
			ws.onclose = function (msg) {
				if (has_error) { return; }
				announce("danger","Verbindung geschlossen! Bitte laden Sie diese Seite neu.");
			};
		} else if ("WebSocket" in window) {
			announce("danger","Interner Fehler! Probieren Sie es später noch einmal.");
		} else {
			announce("info","Die Tabelle ist statisch.<br />Für dynamische Updates brauchen Sie einen Browser, der WebSockets unterstützt.");
		}


		// $.idleTimer(300000); // Hochscrollen nach 5min
		// $(document).bind("idle.idleTimer", function(){
			// $('#page').scrollTop(0);
		// });

	});
