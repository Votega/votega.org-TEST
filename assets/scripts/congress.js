// ---------- CONFIG -------------------------------------------------
const API_ROOT  = 'https://api.congress.gov/v3';
const API_KEY   = 'Oze0IkjnsuXYtNVpM3NXTqHqYRM8jgXnvbdiZVy1';
const MAX_ROWS  = 250;// API max per page
// Updated for JSON format and state filtering
// -------------------------------------------------------------------

const STATES = [
  {code:'AL',name:'Alabama'},{code:'AK',name:'Alaska'},{code:'AZ',name:'Arizona'},
  {code:'AR',name:'Arkansas'},{code:'CA',name:'California'},{code:'CO',name:'Colorado'},
  {code:'CT',name:'Connecticut'},{code:'DE',name:'Delaware'},{code:'FL',name:'Florida'},
  {code:'GA',name:'Georgia'},{code:'HI',name:'Hawaii'},{code:'ID',name:'Idaho'},
  {code:'IL',name:'Illinois'},{code:'IN',name:'Indiana'},{code:'IA',name:'Iowa'},
  {code:'KS',name:'Kansas'},{code:'KY',name:'Kentucky'},{code:'LA',name:'Louisiana'},
  {code:'ME',name:'Maine'},{code:'MD',name:'Maryland'},{code:'MA',name:'Massachusetts'},
  {code:'MI',name:'Michigan'},{code:'MN',name:'Minnesota'},{code:'MS',name:'Mississippi'},
  {code:'MO',name:'Missouri'},{code:'MT',name:'Montana'},{code:'NE',name:'Nebraska'},
  {code:'NV',name:'Nevada'},{code:'NH',name:'New Hampshire'},{code:'NJ',name:'New Jersey'},
  {code:'NM',name:'New Mexico'},{code:'NY',name:'New York'},{code:'NC',name:'North Carolina'},
  {code:'ND',name:'North Dakota'},{code:'OH',name:'Ohio'},{code:'OK',name:'Oklahoma'},
  {code:'OR',name:'Oregon'},{code:'PA',name:'Pennsylvania'},{code:'RI',name:'Rhode Island'},
  {code:'SC',name:'South Carolina'},{code:'SD',name:'South Dakota'},{code:'TN',name:'Tennessee'},
  {code:'TX',name:'Texas'},{code:'UT',name:'Utah'},{code:'VT',name:'Vermont'},
  {code:'VA',name:'Virginia'},{code:'WA',name:'Washington'},{code:'WV',name:'West Virginia'},
  {code:'WI',name:'Wisconsin'},{code:'WY',name:'Wyoming'}
];

const stateSel    = document.getElementById('stateSelect');
const chamberSel  = document.getElementById('chamberSelect');
const memberSel   = document.getElementById('memberSelect');
const statusLine  = document.getElementById('status');
const form        = document.getElementById('lookupForm');

// populate state dropdown once
STATES.forEach(s => {
  const opt=document.createElement('option');
  opt.value=s.code;
  opt.textContent=s.name;
  stateSel.appendChild(opt);
});

chamberSel.addEventListener('change', loadMembers);
stateSel  .addEventListener('change', loadMembers);

// Load members

async function loadMembers () {
  const state   = stateSel.value;
  const chamber = chamberSel.value;

  memberSel.disabled = true;
  memberSel.innerHTML = '';
  if (!state || !chamber) return;

  statusLine.textContent = 'Loading legislators…';
  try {
    let page = 1, results = [];
    while (true) {
      const url = `${API_ROOT}/member?state=${state}&chamber=${chamber}` +
                  `&pageSize=${MAX_ROWS}&page=${page}&format=json&api_key=${API_KEY}`;
      console.log('GET', url);                    // easier to inspect in Network tab
      const res  = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      const rows = data.members  ||                // new docs
                   data.member   || [];            // legacy single-page format
      results.push(...rows);

      const last = data.pagination?.pageCount || 1;
      if (page >= last) break;
      page++;
    }

    // Filter by state name since API uses full names
    const stateName = STATES.find(s => s.code === state)?.name;
    results = results.filter(m => m && typeof m === 'object' && m.state === stateName && m.name);

    if (results.length === 0) {
      throw new Error('No members returned – check state/chamber.');
    }

    results.sort((a,b) => a.name.localeCompare(b.name));
    memberSel.innerHTML = '<option value="">— choose —</option>' +
      results.map(m =>
        `<option value="${m.bioguideId}">
           ${m.name} (${m.partyName})
         </option>`
      ).join('');
    memberSel.disabled = false;
    statusLine.textContent = '';

  } catch (err) {
    console.error('loadMembers()', err);
    statusLine.textContent = err.message.includes('HTTP') ?
      'API error: ' + err.message :
      'Could not load data. Check the console.';
  }
}
// My-Representatives.html form submission. Fetches and displays details for the selected member.
form.addEventListener('submit',e=>{
  e.preventDefault();
  const bioguideId = memberSel.value;
  if (!bioguideId) {
    statusLine.textContent = 'Please select a member.';
    return;
  }
  // Redirect to the member details page
  window.location.href = `member.html?bioguideId=${bioguideId}`;
});

