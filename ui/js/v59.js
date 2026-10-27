/* V5.9 - Stock ADMIN, guichet AGENT et validation CONTROLLER. */
let v59Stocks=[];
async function v59LoadStock(){
 try{
  const [countries,stocks]=await Promise.all([api('/countries'),api('/v59/stocks')]);
  $('#v59Country').innerHTML=countries.map(c=>`<option value="${c.id}">${esc(c.name)}</option>`).join('');
  $('#v59Stocks').innerHTML=table(['Pays','Tarif','Créés','Vendus','Disponibles'],stocks.map(s=>`<tr><td>${esc(countries.find(c=>c.id===s.country_id)?.name||s.country_id)}</td><td>${fmtMoney(s.fare)}</td><td>${s.created}</td><td>${s.sold}</td><td>${s.available}</td></tr>`));
 }catch(e){alert(e.message)}
}
async function v59CreateStock(){
 try{
  const country_id=Number($('#v59Country').value),fare=Number($('#v59Fare').value),quantity=Number($('#v59StockQty').value);
  if(!Number.isSafeInteger(fare)||fare<=0||!Number.isSafeInteger(quantity)||quantity<=0)throw Error('Tarif et quantité invalides');
  if(!confirm(`Créer ${quantity} voyages à ${fmtMoney(fare)} ?`))return;
  await api('/v59/stocks',{method:'POST',body:JSON.stringify({country_id,fare,quantity})});await v59LoadStock();
 }catch(e){alert(e.message)}
}
async function v59LoadSale(){
 try{
  const [stocks,countries]=await Promise.all([api('/v59/stocks'),api('/countries')]);
  v59Stocks=stocks.filter(s=>s.available>0);
  $('#v59SaleStock').innerHTML=v59Stocks.map(s=>`<option value="${s.id}">${esc(countries.find(c=>c.id===s.country_id)?.name||s.country_id)} · ${fmtMoney(s.fare)} · ${s.available} disponibles</option>`).join('');
  v59Preview();
  const c=await api('/cash/sessions/current');$('#saleCashStatus').textContent=c.open?'Caisse ouverte':'Caisse fermée : ouvrez votre caisse avant la vente';
  $('#v59Sell').disabled=!c.open||!v59Stocks.length;
 }catch(e){$('#saleCashStatus').textContent=e.message;$('#v59Sell').disabled=true}
}
function v59Preview(){
 const s=v59Stocks.find(s=>s.id===Number($('#v59SaleStock').value));const q=Number($('#v59Quantity').value);
 $('#v59Total').textContent=s&&Number.isSafeInteger(q)&&q>0?`Total : ${fmtMoney(s.fare*q)} · Stock restant après vente : ${s.available-q}`:'Choisissez un stock et une quantité';
}
async function v59Sell(){
 const b=$('#v59Sell');b.disabled=true;
 try{
  const stock_id=Number($('#v59SaleStock').value),quantity=Number($('#v59Quantity').value);
  if(!Number.isSafeInteger(quantity)||quantity<1||quantity>100)throw Error('Quantité invalide (1 à 100)');
  if(!confirm(`Confirmer l'encaissement de ${quantity} voyage(s) ?`))return;
  const p=await api('/v59/sales',{method:'POST',body:JSON.stringify({stock_id,quantity,provider:'CASH'})});
  const payload=p.code+'|'+p.signature;
  $('#v59Receipt').innerHTML=`<h2>Vente confirmée</h2><p>${p.quantity} voyage(s) · ${fmtMoney(p.total)}</p><p>Valable jusqu'au ${fmtDate(p.valid_until)}</p><p>Code : <b>${esc(p.code)}</b></p><div id="v59Qr"></div><p class="mono">${esc(payload)}</p><button onclick="window.print()">Imprimer</button>`;
  // Le QR est récupéré avec le JWT de l'agent ; aucun lien public non authentifié.
  const r=await fetch('/v59/passes/'+encodeURIComponent(p.code)+'/qr',{headers:{Authorization:'Bearer '+tok}});
  if(r.ok){const url=URL.createObjectURL(await r.blob());const img=document.createElement('img');img.className='qr';img.src=url;img.onload=()=>URL.revokeObjectURL(url);$('#v59Qr').append(img)}
  await v59LoadSale();
 }catch(e){alert(e.message)}finally{b.disabled=false}
}
async function v59LoadTrips(){
 try{const t=await api('/trips');$('#v59BoardTrip').innerHTML=t.filter(x=>['SCHEDULED','IN_PROGRESS'].includes(val(x.status))).map(x=>`<option value="${x.id}">#${x.id} · ${esc(x.line||x.line_id)} · ${fmtDate(x.departure_at)}</option>`).join('')}
 catch(e){$('#result').textContent=e.message}
}
// Remplace le contrôle historique dans l'interface ; les anciens tickets restent en base.
validateTicket=async function(){
 const a=$('#payload').value.trim().split('|');
 if(a.length!==2||!a[0].startsWith('BT-')){$('#result').textContent='QR V5.9 invalide';return}
 try{const d=await api('/v59/boardings',{method:'POST',body:JSON.stringify({code:a[0],signature:a[1],trip_id:Number($('#v59BoardTrip').value)})});
 $('#result').innerHTML=`<div class="ok">Embarquement validé · ${d.remaining} voyage(s) restant(s) · ${d.places_restantes} place(s) libre(s)</div>`}
 catch(e){$('#result').innerHTML=`<div class="bad">Refus : ${esc(e.message)}</div>`}
};
