let tok=localStorage.bt_token||"";
let currentUser=null;
const ROLE_PAGES={ADMIN:["dash","network","fleet","trips","stock","cash","history","scan","users"],AGENT:["sale","cash"],CONTROLLER:["scan"],DRIVER:["driverView"]};
const $=s=>document.querySelector(s);

async function api(p,o={}){
  let h={"Content-Type":"application/json",...(o.headers||{})};
  if(tok)h.Authorization="Bearer "+tok;
  let r=await fetch(p,{...o,headers:h});
  let d=await r.json();
  if(!r.ok){let m=d?.detail?.message||d?.detail||JSON.stringify(d);throw Error(typeof m==="string"?m:JSON.stringify(m));}
  return d;
}

async function login(){
  try{
    let d=await api("/auth/login",{method:"POST",body:JSON.stringify({username:$("#user").value,password:$("#pass").value})});
    tok=d.access_token;localStorage.bt_token=tok;await show();
  }catch(e){$("#err").textContent=e.message}
}
function logout(){localStorage.clear();location.reload()}

function page(id){
  const allowed=ROLE_PAGES[currentUser?.role]||[];
  if(!allowed.includes(id))return;
  ["dash","network","fleet","trips","sale","stock","cash","history","scan","users","driverView"].forEach(x=>$("#"+x).classList.toggle("hide",x!==id));
  if(id==="dash")dashboard();
  if(id==="history")loadHistory();
  if(id==="users"){loadUsers();loadUserAudit();}
  if(id==="fleet")loadFleet();
  if(id==="trips")loadOperations();
  if(id==="sale")v59LoadSale();
   if(id==="stock")v59LoadStock();
   if(id==="scan")v59LoadTrips();
  if(id==="cash"){if(currentUser.role==="ADMIN")loadCash();loadSession();}
  if(id==="driverView")loadDriverTrips();
}
async function loadDriverTrips(){
 try{const t=await api("/trips");$("#driverTrips").innerHTML=table(["Course","Ligne","Départ","Statut"],t.map(x=>`<tr><td>#${x.id}</td><td>${esc(x.line)}</td><td>${fmtDate(x.departure_at)}</td><td>${pill(x.status)}</td></tr>`));}
 catch(e){$("#driverTrips").textContent=e.message;}
}

function table(h,r){return "<table><tr>"+h.map(x=>"<th>"+x+"</th>").join("")+"</tr>"+r.join("")+"</table>"}
function val(x){return x?.value||x}
function esc(x){return String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
function fmtDate(x){return x?new Date(x).toLocaleString("fr-FR"):"—"}
function fmtMoney(x){return new Intl.NumberFormat("fr-FR").format(Number(x||0))+" XAF"}
function pill(x){let v=val(x)||"—";return `<span class="pill ${esc(v)}">${esc(v)}</span>`}

let cache={countries:[],lines:[],vehicles:[],trips:[],drivers:[],assignments:[],maintenance:[],fuel:[],fleetDashboard:null,operationsDashboard:null};
function countryName(id){return cache.countries.find(x=>x.id==id)?.name||id}
function lineName(id){return cache.lines.find(x=>x.id==id)?.name||id}
function vehicleName(id){let v=cache.vehicles.find(x=>x.id==id);return v?`${v.code} - ${v.plate}`:id}
function driverName(id){let d=cache.drivers.find(x=>x.id==id);return d?`${d.first_name} ${d.last_name}`:id}

async function load(){
  let [c,l,v,t]=await Promise.all([api("/countries"),api("/lines"),api("/vehicles"),api("/trips")]);
  cache.countries=c;cache.lines=l;cache.vehicles=v;cache.trips=t;
  let co=c.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join("");
  $("#lc").innerHTML=$("#vc").innerHTML=co;
  let cf=$("#countryFilter");
  if(cf&&cf.options.length<=1)cf.innerHTML='<option value="">Tous les pays</option>'+co;
  $("#tl").innerHTML=l.map(x=>`<option value="${x.id}">${esc(x.code)} - ${esc(x.name)}</option>`).join("");
  $("#tv").innerHTML=v.map(x=>`<option value="${x.id}">${esc(x.code)} - ${esc(x.plate)}</option>`).join("");
  fillSaleTrips();

  let q=($("#networkSearch")?.value||"").toLowerCase(),f=$("#countryFilter")?.value||"";
  let lf=l.filter(x=>(!f||x.country_id==f)&&(`${x.code} ${x.name}`.toLowerCase().includes(q)));
  let vf=v.filter(x=>(!f||x.country_id==f)&&(`${x.code} ${x.plate} ${x.brand||""} ${x.model||""}`.toLowerCase().includes(q)));
  $("#lines").innerHTML=table(["Pays","Code","Nom","Tarif"],lf.map(x=>`<tr><td>${esc(countryName(x.country_id))}</td><td>${esc(x.code)}</td><td>${esc(x.name)}</td><td>${fmtMoney(x.fare)}</td></tr>`));
  $("#vehicles").innerHTML=table(["Pays","Code","Plaque","Places","Kilométrage","Statut"],vf.map(x=>`<tr><td>${esc(countryName(x.country_id))}</td><td>${esc(x.code)}</td><td>${esc(x.plate)}</td><td>${x.capacity}</td><td>${Number(x.mileage||0).toLocaleString("fr-FR")} km</td><td>${pill(x.status)}</td></tr>`));
  if($("#tripsTable"))renderOperations();
}

async function loadHistory(){
  try{
    let [ts,ps]=await Promise.all([api("/tickets"),api("/payments")]);
    let q=($("#ticketSearch")?.value||"").toLowerCase(),s=$("#ticketStatus")?.value||"";
    ts=ts.filter(x=>(!s||val(x.status)===s)&&x.code.toLowerCase().includes(q));
    ps=ps.filter(x=>`${x.reference} ${x.provider}`.toLowerCase().includes(q));
    $("#ticketsTable").innerHTML=table(["Code","Course","Montant","Statut","Expiration","Utilisé"],ts.map(x=>`<tr><td class="mono">${esc(x.code)}</td><td>#${x.trip_id}</td><td>${fmtMoney(x.amount)}</td><td>${pill(x.status)}</td><td>${fmtDate(x.expires_at)}</td><td>${fmtDate(x.used_at)}</td></tr>`));
    $("#paymentsTable").innerHTML=table(["Référence","Ticket","Opérateur","Montant","Statut"],ps.map(x=>`<tr><td class="mono">${esc(x.reference)}</td><td>#${x.ticket_id}</td><td>${esc(x.provider)}</td><td>${fmtMoney(x.amount)}</td><td>${pill(x.status)}</td></tr>`));
  }catch(e){alert(e.message)}
}

async function dashboard(){
  let d=await api("/dashboard");
  let a=[["CA",fmtMoney(d.revenue)],["Tickets",d.tickets],["Utilisés",d.tickets_used],["Paiements",d.successful_payments],["Lignes",d.lines],["Véhicules",d.vehicles],["Courses",d.trips],["Pays",d.countries]];
  $("#kpis").innerHTML=a.map(x=>`<div class="card kpi"><b>${x[1]}</b>${x[0]}</div>`).join("")
}

async function addLine(){
  try{await api("/lines",{method:"POST",body:JSON.stringify({country_id:+$("#lc").value,code:$("#lcode").value,name:$("#lname").value,fare:+$("#fare").value})});await load();alert("Ligne enregistrée")}
  catch(e){alert(e.message)}
}
async function addVehicle(){
  try{
    await api("/vehicles",{method:"POST",body:JSON.stringify({
      country_id:+$("#vc").value,code:$("#vcode").value,plate:$("#plate").value,capacity:+$("#cap").value,status:"ACTIVE",
      brand:$("#vbrand").value||null,model:$("#vmodel").value||null,year:$("#vyear").value?+$("#vyear").value:null,mileage:+($("#vmileage").value||0)
    })});
    await load();alert("Véhicule enregistré")
  }catch(e){alert(e.message)}
}
async function addTrip(){try{let d=$("#dt").value;if(!d)throw Error("Choisissez la date et l'heure");let dr=$("#td").value;await api("/trips",{method:"POST",body:JSON.stringify({line_id:+$("#tl").value,vehicle_id:+$("#tv").value,departure_at:new Date(d).toISOString(),driver_id:dr?+dr:null,notes:$("#tripNotes").value.trim()||null})});await load();await loadOperations();alert("Course programmée")}catch(e){alert(e.message)}}
async function sell(){try{
 let cs=await api("/cash/sessions/current");if(!cs.open)throw Error("Vous devez ouvrir une caisse avant d’encaisser un paiement");let id=+$("#st").value;if(!id)throw Error("Aucune course disponible");
 let trip=cache.trips.find(x=>x.id===id);if(!trip||!["SCHEDULED","IN_PROGRESS"].includes(val(trip.status)))throw Error("Cette course n'est plus disponible à la vente");
 $("#sellBtn").disabled=true;$("#sellBtn").textContent="Encaissement...";
 let t=await api("/tickets",{method:"POST",body:JSON.stringify({trip_id:id})});
 let p=await api(`/tickets/${t.id}/payment`,{method:"POST",body:JSON.stringify({provider:"SIMULATOR",simulate_success:true})});
 $("#ticket").innerHTML=`<h2>Billet payé</h2><div class="ticket-success">Paiement confirmé</div><img class="qr" src="/tickets/${t.code}/qr"><div class="ticket-line"><b>${esc(trip.line||lineName(trip.line_id))}</b></div><p>Course #${id} · ${fmtDate(trip.departure_at)}</p><h2>${fmtMoney(t.amount)}</h2><p>${pill(p.ticket_status)}</p><small class="mono">${esc(t.code)}</small><br><button onclick="window.print()">Imprimer le billet</button>`;
 if(currentUser?.role==="ADMIN")await Promise.all([dashboard(),loadHistory(),loadOperations()]);
  else {await loadSession();await loadSale();}
  renderSaleTrip();
}catch(e){alert(e.message)}finally{$("#sellBtn").textContent="Créer et payer";await saleSessionStatus();}}
async function validateTicket(){let a=$("#payload").value.trim().split("|");if(a.length!==2){$("#result").innerHTML='<div class="bad">QR illisible</div>';return}try{let d=await api("/tickets/validate",{method:"POST",body:JSON.stringify({code:a[0],signature:a[1]})});$("#result").innerHTML=d.valid?`<div class="ok">✓ TICKET VALIDE<br><small>${esc(d.code)}</small></div>`:`<div class="bad">✕ REFUSÉ<br><small>${esc(d.reason)}</small></div>`}catch(e){alert(e.message)}}

/* ========================= V4 FLOTTE ========================= */
function fleetTab(id,btn){
  document.querySelectorAll(".fleet-panel").forEach(x=>x.classList.toggle("hide",x.id!==id));
  document.querySelectorAll(".tabs .tab").forEach(x=>x.classList.remove("active"));
  if(btn)btn.classList.add("active");
}
function options(rows,label,filter=()=>true){return rows.filter(filter).map(x=>`<option value="${x.id}">${esc(label(x))}</option>`).join("")}

async function loadFleet(){
  try{
    let [d,drivers,assignments,maintenance,fuel,vehicles,countries]=await Promise.all([
      api("/fleet/dashboard"),api("/drivers"),api("/driver-assignments"),api("/maintenance"),api("/fuel"),api("/vehicles"),api("/countries")
    ]);
    cache.fleetDashboard=d;cache.drivers=drivers;cache.assignments=assignments;cache.maintenance=maintenance;cache.fuel=fuel;cache.vehicles=vehicles;cache.countries=countries;
    renderFleetKpis();renderFleetVehicles();renderDrivers();renderAssignments();renderMaintenance();renderFuel();fillFleetForms();
  }catch(e){alert(e.message)}
}

function renderFleetKpis(){
  let d=cache.fleetDashboard||{};
  let a=[
    ["Véhicules",d.vehicles||0],["Actifs",d.vehicles_active||0],["Maintenance",d.vehicles_maintenance||0],["Hors service",d.vehicles_out_of_service||0],
    ["Chauffeurs actifs",d.drivers_active||0],["Affectations",d.active_assignments||0],["Carburant",fmtMoney(d.fuel_cost)],["Maintenance",fmtMoney(d.maintenance_cost)]
  ];
  $("#fleetKpis").innerHTML=a.map(x=>`<div class="card kpi"><b>${x[1]}</b>${x[0]}</div>`).join("");
}
function renderFleetVehicles(){
  let q=($("#fleetVehicleSearch")?.value||"").toLowerCase(),s=$("#fleetVehicleStatus")?.value||"";
  let rows=cache.vehicles.filter(v=>(!s||v.status===s)&&`${v.code} ${v.plate} ${v.brand||""} ${v.model||""}`.toLowerCase().includes(q));
  $("#fleetVehiclesTable").innerHTML=table(["Code","Plaque","Marque / modèle","Année","Places","Kilométrage","Statut"],rows.map(v=>`<tr>
    <td><b>${esc(v.code||"—")}</b></td><td>${esc(v.plate)}</td><td>${esc([v.brand,v.model].filter(Boolean).join(" ")||"—")}</td>
    <td>${v.year||"—"}</td><td>${v.capacity}</td><td class="nowrap">${Number(v.mileage||0).toLocaleString("fr-FR")} km</td><td>${pill(v.status)}</td>
  </tr>`));
}
function renderDrivers(){
  $("#driversTable").innerHTML=table(["Matricule","Chauffeur","Téléphone","Permis","Statut"],cache.drivers.map(d=>`<tr><td><b>${esc(d.employee_code)}</b></td><td>${esc(d.first_name)} ${esc(d.last_name)}</td><td>${esc(d.phone||"—")}</td><td>${esc(d.license_number)}</td><td>${pill(d.status)}</td></tr>`));
}
function renderAssignments(){
  $("#assignmentsTable").innerHTML=table(["Chauffeur","Véhicule","Début","Fin","Statut","Action"],cache.assignments.map(a=>`<tr><td>${esc(a.driver||driverName(a.driver_id))}</td><td>${esc(a.vehicle||vehicleName(a.vehicle_id))}</td><td>${fmtDate(a.started_at)}</td><td>${fmtDate(a.ended_at)}</td><td>${pill(a.active?"ACTIVE":"ENDED")}</td><td>${a.active?`<button class="action danger" onclick="endAssignment(${a.id})">Terminer</button>`:"—"}</td></tr>`));
}
function renderMaintenance(){
  $("#maintenanceTable").innerHTML=table(["Véhicule","Type","Description","Km","Coût","Statut","Prochaine","Action"],cache.maintenance.map(m=>`<tr><td>${esc(m.vehicle||vehicleName(m.vehicle_id))}</td><td>${esc(m.maintenance_type||"—")}</td><td>${esc(m.description)}</td><td>${m.mileage==null?"—":Number(m.mileage).toLocaleString("fr-FR")+" km"}</td><td class="money">${fmtMoney(m.cost)}</td><td>${pill(m.status)}</td><td>${fmtDate(m.next_maintenance_at)}</td><td>${m.status!=="COMPLETED"?`<button class="action gold" onclick="completeMaintenance(${m.id})">Terminer</button>`:"—"}</td></tr>`));
}
function renderFuel(){
  $("#fuelTable").innerHTML=table(["Date","Véhicule","Chauffeur","Litres","Coût","Km"],cache.fuel.map(f=>`<tr><td>${fmtDate(f.created_at)}</td><td>${esc(f.vehicle||vehicleName(f.vehicle_id))}</td><td>${esc(f.driver||"—")}</td><td>${Number(f.liters).toLocaleString("fr-FR")} L</td><td class="money">${fmtMoney(f.cost)}</td><td>${f.mileage==null?"—":Number(f.mileage).toLocaleString("fr-FR")+" km"}</td></tr>`));
}
function fillFleetForms(){
  $("#driverCountry").innerHTML=options(cache.countries,x=>x.name);
  let activeDrivers=options(cache.drivers,x=>`${x.employee_code} - ${x.first_name} ${x.last_name}`,x=>x.status==="ACTIVE");
  let activeVehicles=options(cache.vehicles,x=>`${x.code} - ${x.plate}`,x=>x.status==="ACTIVE");
  $("#assignmentDriver").innerHTML=activeDrivers;
  $("#assignmentVehicle").innerHTML=activeVehicles;
  $("#maintenanceVehicle").innerHTML=options(cache.vehicles,x=>`${x.code} - ${x.plate}`);
  $("#fuelVehicle").innerHTML=options(cache.vehicles,x=>`${x.code} - ${x.plate}`);
  $("#fuelDriver").innerHTML='<option value="">Sans chauffeur</option>'+activeDrivers;
}

async function addDriver(){
  try{
    await api("/drivers",{method:"POST",body:JSON.stringify({
      country_id:+$("#driverCountry").value,employee_code:$("#driverCode").value.trim(),first_name:$("#driverFirstName").value.trim(),
      last_name:$("#driverLastName").value.trim(),phone:$("#driverPhone").value.trim()||null,license_number:$("#driverLicense").value.trim(),status:"ACTIVE"
    })});
    ["driverCode","driverFirstName","driverLastName","driverPhone","driverLicense"].forEach(id=>$("#"+id).value="");
    await loadFleet();alert("Chauffeur enregistré")
  }catch(e){alert(e.message)}
}
async function addAssignment(){
  try{
    await api("/driver-assignments",{method:"POST",body:JSON.stringify({driver_id:+$("#assignmentDriver").value,vehicle_id:+$("#assignmentVehicle").value})});
    await loadFleet();alert("Affectation enregistrée")
  }catch(e){alert(e.message)}
}
async function endAssignment(id){
  if(!confirm("Terminer cette affectation ?"))return;
  try{await api(`/driver-assignments/${id}/end`,{method:"PUT"});await loadFleet()}catch(e){alert(e.message)}
}
function isoOrNull(id){let v=$("#"+id).value;return v?new Date(v).toISOString():null}
async function addMaintenance(){
  try{
    await api("/maintenance",{method:"POST",body:JSON.stringify({
      vehicle_id:+$("#maintenanceVehicle").value,description:$("#maintenanceDescription").value.trim(),maintenance_type:$("#maintenanceType").value.trim()||null,
      cost:+($("#maintenanceCost").value||0),mileage:$("#maintenanceMileage").value?+$("#maintenanceMileage").value:null,
      scheduled_at:isoOrNull("maintenanceScheduled"),next_maintenance_at:isoOrNull("maintenanceNext"),status:$("#maintenanceStatus").value
    })});
    await loadFleet();await load();alert("Maintenance enregistrée")
  }catch(e){alert(e.message)}
}
async function completeMaintenance(id){
  if(!confirm("Marquer cette maintenance comme terminée et remettre le véhicule en ACTIVE ?"))return;
  try{
    await api(`/maintenance/${id}`,{method:"PUT",body:JSON.stringify({status:"COMPLETED",done:true,completed_at:new Date().toISOString()})});
    await loadFleet();await load()
  }catch(e){alert(e.message)}
}
async function addFuel(){
  try{
    let driver=$("#fuelDriver").value;
    await api("/fuel",{method:"POST",body:JSON.stringify({
      vehicle_id:+$("#fuelVehicle").value,driver_id:driver?+driver:null,liters:+$("#fuelLiters").value,cost:+$("#fuelCost").value,
      mileage:$("#fuelMileage").value?+$("#fuelMileage").value:null
    })});
    $("#fuelLiters").value=$("#fuelCost").value=$("#fuelMileage").value="";
    await loadFleet();await load();alert("Plein enregistré")
  }catch(e){alert(e.message)}
}


/* ====================== V5.2 GUICHET ====================== */
async function loadSale(){try{let [t,l,v,d]=await Promise.all([api("/trips"),api("/lines"),api("/vehicles"),currentUser?.role==="ADMIN"?api("/drivers"):Promise.resolve([])]);cache.trips=t;cache.lines=l;cache.vehicles=v;cache.drivers=d;fillSaleTrips();await saleSessionStatus()}catch(e){alert(e.message)}}
function renderSaleTrip(){let box=$("#saleTripInfo"),btn=$("#sellBtn");if(!box||!btn)return;let id=+($("#st")?.value||0),t=cache.trips.find(x=>x.id===id);if(!t){box.innerHTML='<div class="empty-sale">Aucune course programmée ou en circulation.</div>';btn.disabled=true;return}let line=cache.lines.find(x=>x.id==t.line_id),vehicle=cache.vehicles.find(x=>x.id==t.vehicle_id);box.innerHTML=`<div class="sale-route">${esc(t.line||lineName(t.line_id))}</div><div class="sale-grid"><div><span>Départ</span><b>${fmtDate(t.departure_at)}</b></div><div><span>Statut</span><b>${pill(t.status)}</b></div><div><span>Bus</span><b>${esc(t.vehicle||vehicleName(t.vehicle_id))}</b></div><div><span>Chauffeur</span><b>${esc(t.driver||driverName(t.driver_id)||"Non affecté")}</b></div><div><span>Capacité</span><b>${vehicle?.capacity??"—"} places</b></div><div><span>Tarif</span><b class="sale-fare">${fmtMoney(line?.fare||0)}</b></div></div>`;btn.disabled=$("#saleCashStatus")?.classList.contains("closed")||false}

/* ====================== V5.1 EXPLOITATION ====================== */
async function loadOperations(){try{let [d,t,dr,v,l]=await Promise.all([api("/operations/dashboard"),api("/trips"),api("/drivers"),api("/vehicles"),api("/lines")]);cache.operationsDashboard=d;cache.trips=t;cache.drivers=dr;cache.vehicles=v;cache.lines=l;renderOperationsKpis();fillOperationForms();renderOperations();fillSaleTrips()}catch(e){alert(e.message)}}
function renderOperationsKpis(){let d=cache.operationsDashboard||{};let a=[["Courses",d.trips_total||0],["Programmées",d.scheduled||0],["En circulation",d.in_progress||0],["Terminées",d.completed||0],["Annulées",d.cancelled||0],["Distance",`${Number(d.distance_km||0).toLocaleString("fr-FR")} km`],["Tickets",d.tickets||0],["Recettes",fmtMoney(d.revenue)]];$("#operationsKpis").innerHTML=a.map(x=>`<div class="card kpi"><b>${x[1]}</b>${x[0]}</div>`).join("")}
function fillOperationForms(){if($("#tl"))$("#tl").innerHTML=options(cache.lines,x=>`${x.code} - ${x.name}`);if($("#tv"))$("#tv").innerHTML=options(cache.vehicles,x=>`${x.code} - ${x.plate}`,x=>x.status==="ACTIVE");if($("#td"))$("#td").innerHTML='<option value="">Sans chauffeur</option>'+options(cache.drivers,x=>`${x.employee_code} - ${x.first_name} ${x.last_name}`,x=>x.status==="ACTIVE")}
function fillSaleTrips(){if(!$("#st"))return;let current=$("#st").value;let a=cache.trips.filter(t=>["SCHEDULED","IN_PROGRESS"].includes(val(t.status)));$("#st").innerHTML=a.length?a.map(t=>`<option value="${t.id}">#${t.id} · ${esc(t.line||lineName(t.line_id))} · ${fmtDate(t.departure_at)}</option>`).join(""):'<option value="">Aucune course disponible</option>';if(current&&a.some(t=>String(t.id)===String(current)))$("#st").value=current;renderSaleTrip()}
function operationActions(t){let s=val(t.status);if(s==="SCHEDULED")return `<button class="action gold" onclick="startTrip(${t.id})">Démarrer</button><button class="action danger" onclick="cancelTrip(${t.id})">Annuler</button><button class="action secondary" onclick="showTripReport(${t.id})">Rapport</button>`;if(s==="IN_PROGRESS")return `<button class="action gold" onclick="completeTrip(${t.id})">Terminer</button><button class="action secondary" onclick="showTripReport(${t.id})">Rapport</button>`;return `<button class="action secondary" onclick="showTripReport(${t.id})">Rapport</button>`}
function renderOperations(){let b=$("#tripsTable");if(!b)return;let q=($("#tripSearch")?.value||"").toLowerCase(),s=$("#tripStatusFilter")?.value||"";let a=cache.trips.filter(t=>(!s||val(t.status)===s)&&`${t.id} ${t.line||lineName(t.line_id)} ${t.vehicle||vehicleName(t.vehicle_id)} ${t.driver||""}`.toLowerCase().includes(q));b.innerHTML=table(["ID","Départ prévu","Ligne","Véhicule","Chauffeur","Km","Statut","Actions"],a.map(t=>`<tr><td><b>#${t.id}</b></td><td class="nowrap">${fmtDate(t.departure_at)}</td><td>${esc(t.line||lineName(t.line_id))}</td><td>${esc(t.vehicle||vehicleName(t.vehicle_id))}</td><td>${esc(t.driver||"—")}</td><td>${t.start_mileage==null?"—":Number(t.start_mileage).toLocaleString("fr-FR")+(t.end_mileage==null?"":" → "+Number(t.end_mileage).toLocaleString("fr-FR"))}</td><td>${pill(t.status)}</td><td class="actions">${operationActions(t)}</td></tr>`))}
async function startTrip(id){let t=cache.trips.find(x=>x.id==id),v=cache.vehicles.find(x=>x.id==t?.vehicle_id),km=prompt(`Kilométrage de départ - course #${id}`,v?.mileage??"");if(km===null)return;try{await api(`/trips/${id}/start`,{method:"PUT",body:JSON.stringify({start_mileage:+km})});await loadOperations();await load();alert(`Course #${id} démarrée`)}catch(e){alert(e.message)}}
async function completeTrip(id){let t=cache.trips.find(x=>x.id==id),km=prompt(`Kilométrage d'arrivée - course #${id}`,t?.start_mileage??"");if(km===null)return;try{let r=await api(`/trips/${id}/complete`,{method:"PUT",body:JSON.stringify({end_mileage:+km})});await loadOperations();await load();alert(`Course terminée : ${r.distance_km} km`);await showTripReport(id)}catch(e){alert(e.message)}}
async function cancelTrip(id){let n=prompt(`Motif d'annulation - course #${id}`,"");if(n===null||!confirm("Confirmer l'annulation ?"))return;try{await api(`/trips/${id}/cancel`,{method:"PUT",body:JSON.stringify({notes:n||null})});await loadOperations();await load()}catch(e){alert(e.message)}}
async function showTripReport(id){try{let r=await api(`/trips/${id}/report`);$("#tripReportContent").innerHTML=`<div class="report-grid"><div><span>Course</span><b>#${r.trip_id}</b></div><div><span>Statut</span><b>${pill(r.status)}</b></div><div><span>Ligne</span><b>${esc(r.line||"—")}</b></div><div><span>Véhicule</span><b>${esc(r.vehicle||"—")}</b></div><div><span>Chauffeur</span><b>${esc(r.driver||"—")}</b></div><div><span>Départ prévu</span><b>${fmtDate(r.scheduled_departure)}</b></div><div><span>Départ réel</span><b>${fmtDate(r.actual_departure)}</b></div><div><span>Arrivée</span><b>${fmtDate(r.actual_arrival)}</b></div><div><span>Distance</span><b>${r.distance_km==null?"—":r.distance_km+" km"}</b></div><div><span>Tickets</span><b>${r.tickets_total||0}</b></div><div><span>Utilisés</span><b>${r.tickets_used||0}</b></div><div><span>Paiements</span><b>${r.successful_payments||0}</b></div><div><span>Recettes</span><b>${fmtMoney(r.revenue)}</b></div></div><p class="report-notes"><b>Notes :</b> ${esc(r.notes||"—")}</p>`;$("#tripReport").classList.remove("hide");$("#tripReport").scrollIntoView({behavior:"smooth"})}catch(e){alert(e.message)}}
function closeTripReport(){$("#tripReport").classList.add("hide")}


/* ====================== V5.3 CAISSE ====================== */
function cashToday(){let a=new Intl.DateTimeFormat("en-CA",{timeZone:"Africa/Brazzaville",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date()),p=Object.fromEntries(a.map(x=>[x.type,x.value]));return `${p.year}-${p.month}-${p.day}`}
async function loadCash(){try{let e=$("#cashDate");if(!e.value)e.value=cashToday();let q=encodeURIComponent(e.value),[d,x,l,t]=await Promise.all([api(`/cash/daily?day=${q}`),api(`/cash/daily/details?day=${q}`),api(`/cash/by-line?day=${q}`),api(`/cash/by-trip?day=${q}`)]);$("#cashKpis").innerHTML=[["Recettes",fmtMoney(d.revenue)],["Tickets vendus",d.tickets_sold||0],["Paiements réussis",d.payments_success||0],["Courses encaissées",new Set(x.map(y=>y.trip_id)).size]].map(y=>`<div class="card kpi"><b>${y[1]}</b>${y[0]}</div>`).join("");$("#cashProviders").innerHTML=table(["Opérateur","Paiements","Recettes"],(d.providers||[]).map(y=>`<tr><td><b>${esc(y.provider)}</b></td><td>${y.payments}</td><td class="money">${fmtMoney(y.revenue)}</td></tr>`));$("#cashLines").innerHTML=table(["Ligne","Tickets","Recettes"],l.map(y=>`<tr><td><b>${esc(y.line_code)}</b><br><span class="muted">${esc(y.line_name)}</span></td><td>${y.tickets}</td><td class="money">${fmtMoney(y.revenue)}</td></tr>`));$("#cashTrips").innerHTML=table(["Course","Départ","Ligne","Tickets","Recettes"],t.map(y=>`<tr><td><b>#${y.trip_id}</b></td><td>${fmtDate(y.departure_at)}</td><td>${esc(y.line_code)} - ${esc(y.line_name)}</td><td>${y.tickets}</td><td class="money">${fmtMoney(y.revenue)}</td></tr>`));$("#cashDetails").innerHTML=table(["Heure","Référence","Ticket","Course","Ligne","Opérateur","Montant","Statut"],x.map(y=>`<tr><td>${fmtDate(y.paid_at)}</td><td class="mono">${esc(y.reference)}</td><td class="mono">${esc(y.ticket_code)}</td><td>#${y.trip_id}</td><td>${esc(y.line_code)}</td><td>${esc(y.provider)}</td><td class="money">${fmtMoney(y.amount)}</td><td>${pill(y.payment_status)}</td></tr>`));$("#cashPeriodLabel").textContent=`Journée du ${d.date} · ${d.timezone}`}catch(e){alert(e.message)}}

async function show(){
  try{
    currentUser=await api("/auth/me");
    const allowed=ROLE_PAGES[currentUser.role];
    if(!allowed)throw Error("Rôle non reconnu");
    $("#identity").textContent=`${currentUser.username} · ${currentUser.role}`;
    document.querySelectorAll("aside [data-page]").forEach(b=>b.classList.toggle("hide",!allowed.includes(b.dataset.page)));
    document.querySelectorAll(".admin-cash-report").forEach(e=>e.classList.toggle("hide",currentUser.role!=="ADMIN"));
    $("#login").classList.add("hide");$("#app").classList.remove("hide");
    if(currentUser.role==="ADMIN")await load();
    page(allowed[0]);
  }catch(e){tok="";currentUser=null;localStorage.removeItem("bt_token");$("#app").classList.add("hide");$("#login").classList.remove("hide");$("#err").textContent="Connexion impossible : "+e.message;}
}
if(tok)show();

/* V5.4 — Gestion de sessions de caisse */
let activeSession=null,sessionBusy=false;
function validAmount(id){const s=$(id).value.trim(),n=Number(s);if(!s||!Number.isSafeInteger(n)||n<0)throw Error("Saisissez un montant entier positif ou nul");return n}
async function loadSession(){
 try{
  const r=await api("/cash/sessions/current");activeSession=r.open?r.session:null;
  $("#sessionBadge").textContent=r.open?"OUVERTE":"FERMÉE";
  $("#sessionBadge").className="pill "+(r.open?"ACTIVE":"CANCELLED");
  $("#sessionOpenForm").classList.toggle("hide",r.open);
  $("#sessionCloseForm").classList.toggle("hide",!r.open);
  $("#sessionMessage").textContent=r.open?"Encaissements liés à votre session ouverte.":"Ouvrez une caisse avant d'encaisser.";
  if(r.open){const s=r.session;$("#sessionInfo").textContent=`Session #${s.id} · ${s.username} · ${fmtDate(s.opened_at)}`;
   $("#sessionKpis").innerHTML=[["Fond initial",fmtMoney(s.opening_amount)],["Ventes",fmtMoney(s.sales_revenue)],["Attendu",fmtMoney(s.expected_amount)],["Paiements",s.payments]].map(x=>`<div class="card kpi"><b>${x[1]}</b>${x[0]}</div>`).join("");
   previewDifference();}
 }catch(e){activeSession=null;$("#sessionOpenForm").classList.add("hide");$("#sessionCloseForm").classList.add("hide");$("#sessionMessage").textContent=e.message}
}
function previewDifference(){
 const el=$("#declaredAmount"),out=$("#differencePreview");
 if(!activeSession||!el.value.trim()){out.textContent="Saisissez le montant constaté pour calculer l'écart.";return}
 const n=Number(el.value);out.textContent=Number.isSafeInteger(n)&&n>=0?`Écart estimé : ${fmtMoney(n-Number(activeSession.expected_amount))}`:"Montant invalide";
}
async function openSession(){
 if(sessionBusy)return;
 try{const opening_amount=validAmount("#openingAmount");sessionBusy=true;$("#openSessionBtn").disabled=true;
 await api("/cash/sessions/open",{method:"POST",body:JSON.stringify({opening_amount,notes:$("#openingNotes").value.trim()||null})});
 $("#lastClosure").classList.add("hide");await loadSession();await saleSessionStatus();
 }catch(e){alert(e.message)}finally{sessionBusy=false;$("#openSessionBtn").disabled=false}
}
async function closeSession(){
 if(sessionBusy||!activeSession)return;
 try{const declared_amount=validAmount("#declaredAmount"),s=activeSession;
 if(!confirm(`Clôturer la caisse #${s.id} ?\nAttendu : ${fmtMoney(s.expected_amount)}\nDéclaré : ${fmtMoney(declared_amount)}\nÉcart estimé : ${fmtMoney(declared_amount-s.expected_amount)}`))return;
 sessionBusy=true;$("#closeSessionBtn").disabled=true;
 const d=await api(`/cash/sessions/${s.id}/close`,{method:"POST",body:JSON.stringify({declared_amount,notes:$("#closingNotes").value.trim()||null})});
 $("#lastClosure").innerHTML=`<h3>Clôture #${d.id}</h3><p>Attendu : ${fmtMoney(d.expected_amount)} · Déclaré : ${fmtMoney(d.declared_amount)} · Écart : <b>${fmtMoney(d.difference_amount)}</b></p>`;
 $("#lastClosure").classList.remove("hide");$("#declaredAmount").value="";$("#closingNotes").value="";
 await loadSession();await saleSessionStatus();
 }catch(e){alert(e.message)}finally{sessionBusy=false;$("#closeSessionBtn").disabled=false}
}
async function saleSessionStatus(){
 const el=$("#saleCashStatus"),btn=$("#sellBtn");if(!el)return;
 try{const d=await api("/cash/sessions/current");el.className="cash-sale-status "+(d.open?"opened":"closed");
 el.textContent=d.open?`Caisse #${d.session.id} ouverte · ${d.session.username}`:"Caisse fermée : ouvrez votre caisse dans l'onglet Caisse.";
 btn.disabled=!d.open||!$("#st").value;
 }catch(e){el.className="cash-sale-status closed";el.textContent="Vérification de caisse impossible : "+e.message;btn.disabled=true}
}


/* V5.6 — Gestion des utilisateurs (ADMIN uniquement, contrôle également côté API) */
const ROLE_NAMES={ADMIN:"Administrateur",AGENT:"Agent de guichet",CONTROLLER:"Contrôleur",DRIVER:"Chauffeur"};
async function loadUsers(){
  if(currentUser?.role!=="ADMIN")return;
  const el=$("#usersTable");
  try{
    const users=await api("/users");
    // Chaque ligne offre les opérations d'administration autorisées.
    // Les valeurs sont échappées pour éviter l'injection HTML.
    el.innerHTML=table(["ID","Identifiant","Rôle","Statut","Actions"],users.map(u=>`<tr><td>${Number(u.id)}</td><td>${esc(u.username)}</td><td>${esc(ROLE_NAMES[u.role]||u.role)}</td><td>${u.is_active?"Actif":"Désactivé"}</td><td><button class="secondary compact" onclick="editUserRole(${Number(u.id)},'${esc(u.role)}')">Rôle</button> <button class="secondary compact" onclick="toggleUser(${Number(u.id)},${!u.is_active})" ${u.id===currentUser.id?"disabled":""}>${u.is_active?"Désactiver":"Activer"}</button> <button class="secondary compact" onclick="resetUserPassword(${Number(u.id)})">Mot de passe</button></td></tr>`));
  }catch(e){el.textContent="Impossible de charger les comptes : "+e.message;}
}
async function createUser(event){
  event.preventDefault();
  if(currentUser?.role!=="ADMIN")return;
  const button=$("#createUserBtn"),message=$("#userFormMessage");
  const username=$("#newUsername").value.trim();
  const password=$("#newPassword").value;
  const role=$("#newRole").value;
  if(!username||!password){message.textContent="Identifiant et mot de passe requis.";return;}
  if(role==="ADMIN"&&!confirm("Créer un compte administrateur avec accès étendu ?"))return;
  button.disabled=true;message.textContent="Création en cours…";
  try{
    const created=await api("/users",{method:"POST",body:JSON.stringify({username,password,role})});
    $("#newPassword").value="";
    $("#newUsername").value="";
    $("#newRole").value="AGENT";
    message.textContent=`Compte ${created.username} créé (${ROLE_NAMES[created.role]||created.role}).`;
    await loadUsers();
  }catch(e){message.textContent="Création impossible : "+e.message;}
  finally{button.disabled=false;}
}

// ============================================================
// V5.7 : administration sécurisée des comptes
// ============================================================
// Les contrôles côté navigateur facilitent l'usage ; l'API reste responsable
// de toutes les autorisations et interdit l'auto-désactivation.
async function editUserRole(id,oldRole){
  const role=prompt("Nouveau rôle : ADMIN, AGENT, CONTROLLER ou DRIVER",oldRole);
  if(role===null)return;
  const selected=role.trim().toUpperCase();
  if(!["ADMIN","AGENT","CONTROLLER","DRIVER"].includes(selected)){alert("Rôle invalide");return;}
  if(!confirm(`Changer le rôle du compte #${id} en ${selected} ?`))return;
  try{await api(`/users/${id}/role`,{method:"PATCH",body:JSON.stringify({role:selected})});await loadUsers();}
  catch(e){alert(e.message)}
}
async function toggleUser(id,active){
  if(!confirm(`${active?"Réactiver":"Désactiver"} le compte #${id} ?`))return;
  try{await api(`/users/${id}/status?active=${active}`,{method:"PATCH"});await loadUsers();}
  catch(e){alert(e.message)}
}
async function resetUserPassword(id){
  const password=prompt(`Nouveau mot de passe pour le compte #${id} (12 caractères minimum) :`);
  if(password===null)return;
  if(password.length<12){alert("12 caractères minimum");return;}
  if(!confirm(`Réinitialiser le mot de passe du compte #${id} ? Les anciennes sessions seront invalidées.`))return;
  try{await api(`/users/${id}/reset-password`,{method:"POST",body:JSON.stringify({password})});alert("Mot de passe modifié");}
  catch(e){alert(e.message)}
}
async function loadUserAudit(){
  try{
    const records=await api("/users/audit?limit=100");
    $("#userAuditTable").innerHTML=table(["Date","Utilisateur","Action","Cible"],records.map(a=>`<tr><td>${fmtDate(a.created_at)}</td><td>${esc(a.username)}</td><td>${esc(a.action)}</td><td>${esc(a.target)}</td></tr>`));
  }catch(e){$("#userAuditTable").textContent=e.message;}
}
