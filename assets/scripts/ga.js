// ---------- CONFIG -------------------------------------------------
const DATA_URL = 'assets/data/ga-members.json';
// -------------------------------------------------------------------

const chamberSel  = document.getElementById('chamberSelect');
const districtSel = document.getElementById('districtSelect');
const statusLine  = document.getElementById('status');
const form        = document.getElementById('lookupForm');

let allMembers = [];

function partyAbbrev(party) {
  if (!party) return '';
  const p = party.toLowerCase();
  if (p.startsWith('r')) return 'R';
  if (p.startsWith('d')) return 'D';
  return party[0].toUpperCase();
}

function getBasePath() {
  return window.location.pathname.includes('/votega.org-TEST/') ? '/votega.org-TEST/' : '/';
}

async function loadData() {
  statusLine.textContent = 'Loading member data…';
  try {
    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    allMembers = data.members || [];
    statusLine.textContent = '';
  } catch (err) {
    statusLine.textContent = 'Could not load GA member data: ' + err.message;
  }
}

function populateDistricts() {
  const chamber = chamberSel.value;
  districtSel.innerHTML = '<option value="">— choose district —</option>';
  districtSel.disabled = true;

  if (!chamber || allMembers.length === 0) return;

  const chamberName = chamber === 'senate' ? 'Senate' : 'House of Representatives';

  const members = allMembers
    .filter(m => m.chamber === chamberName)
    .sort((a, b) => (a.district ?? 999) - (b.district ?? 999));

  members.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    const abbrev = partyAbbrev(m.party);
    opt.textContent = `District ${m.district} — ${m.name}${abbrev ? ` (${abbrev})` : ''}`;
    districtSel.appendChild(opt);
  });

  districtSel.disabled = false;
}

chamberSel.addEventListener('change', populateDistricts);

form.addEventListener('submit', e => {
  e.preventDefault();
  const id = districtSel.value;
  if (!id) {
    statusLine.textContent = 'Please select a district.';
    return;
  }
  window.location.href = `${getBasePath()}ga-member.html?id=${encodeURIComponent(id)}`;
});

loadData();
