/**
 * House of Israel – helper that runs inside Rebekah's Google account.
 * Every 10 minutes it:
 *  1. emails the administrator about each new access request,
 *  2. emails each newly approved member their sign-in details,
 *  3. copies members, the teaching schedule and quizzes into the
 *     "House of Israel – data" Google Sheet that the weekly emails read.
 * Run setup() once to create the sheet and the 10-minute trigger.
 */
const PROJECT = 'house-of-israel';
const ADMIN_EMAILS = 'rebekahzadokmugisha@gmail.com,zadokitefamily@gmail.com';
const SITE = 'https://rebekahzadokmugisha-boop.github.io/houseofisrael/';
const FIRST_PASSWORD = 'Pesach753';
const BASE = 'https://firestore.googleapis.com/v1/projects/' + PROJECT + '/databases/(default)/documents/';

function setup() {
  const props = PropertiesService.getScriptProperties();
  if (!props.getProperty('SHEET_ID')) {
    const ss = SpreadsheetApp.create('House of Israel – data');
    props.setProperty('SHEET_ID', ss.getId());
  }
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('run').timeBased().everyMinutes(10).create();
  run();
  Logger.log('Sheet: ' + SpreadsheetApp.openById(props.getProperty('SHEET_ID')).getUrl());
}

function fs_(method, path, body) {
  const res = UrlFetchApp.fetch(BASE + path, {
    method: method,
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': PROJECT },
    payload: body ? JSON.stringify(body) : undefined,
    muteHttpExceptions: true
  });
  if (res.getResponseCode() >= 300) throw new Error(path + ' ' + res.getResponseCode() + ' ' + res.getContentText());
  return JSON.parse(res.getContentText() || '{}');
}
function val_(v) {
  if (!v) return null;
  if ('stringValue' in v) return v.stringValue;
  if ('integerValue' in v) return Number(v.integerValue);
  if ('doubleValue' in v) return v.doubleValue;
  if ('booleanValue' in v) return v.booleanValue;
  if ('nullValue' in v) return null;
  if ('mapValue' in v) { const o = {}; const f = v.mapValue.fields || {}; Object.keys(f).forEach(k => o[k] = val_(f[k])); return o; }
  if ('arrayValue' in v) return (v.arrayValue.values || []).map(val_);
  return null;
}
function list_(coll) {
  let out = [], token = '';
  do {
    const r = fs_('get', coll + '?pageSize=300' + (token ? '&pageToken=' + token : ''));
    (r.documents || []).forEach(d => { const o = val_({ mapValue: { fields: d.fields || {} } }); o._id = d.name.split('/').pop(); out.push(o); });
    token = r.nextPageToken || '';
  } while (token);
  return out;
}
function get_(path) { try { const d = fs_('get', path); return val_({ mapValue: { fields: d.fields || {} } }); } catch (e) { return null; } }
function mark_(path, field) {
  const body = { fields: {} }; body.fields[field] = { booleanValue: true };
  fs_('patch', path + '?updateMask.fieldPaths=' + field, body);
}

function run() {
  // 1. new requests -> tell the administrator
  const apps = list_('applications');
  apps.filter(a => a.status === 'pending' && !a.notified).forEach(a => {
    MailApp.sendEmail({
      to: ADMIN_EMAILS,
      subject: 'House of Israel: new access request from ' + a.name,
      body: a.name + ' has asked to join the House of Israel app.\n\nEmail: ' + a.email + '\nPhone: ' + a.phone +
        '\n\nApprove or decline here: ' + SITE + '#admin',
      name: 'House of Israel'
    });
    mark_('applications/' + a._id, 'notified');
  });
  // 2. newly approved members -> welcome email with first password
  const members = list_('members');
  members.filter(m => !m.revoked && !m.welcomed && m.email).forEach(m => {
    const first = String(m.name || '').split(' ')[0] || 'friend';
    MailApp.sendEmail({
      to: m.email,
      subject: 'Welcome to the House of Israel app',
      body: 'Shalom ' + first + ',\n\nYou now have access to the House of Israel app: the moon calendar, the weekly Torah portion, the Scriptures, the hymn book and the weekly quiz.\n\n' +
        'Open: ' + SITE + '\nEmail: ' + m.email + '\nFirst password: ' + FIRST_PASSWORD +
        '\n\nThe app will ask you to choose your own password after you sign in.\n\nHouse of Israel',
      name: 'House of Israel'
    });
    mark_('members/' + m._id, 'welcomed');
  });
  // 3. copy to the sheet for the weekly emails
  const ss = SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty('SHEET_ID'));
  write_(ss, 'Members', ['Name', 'Email', 'Phone', 'Approved', 'Active'],
    members.map(m => [m.name || '', m.email || '', m.phone || '', m.approvedAt ? new Date(m.approvedAt) : '', m.revoked ? 'no' : 'yes']));
  write_(ss, 'Requests', ['Name', 'Email', 'Phone', 'Status', 'Applied'],
    apps.map(a => [a.name || '', a.email || '', a.phone || '', a.status || '', a.createdAt ? new Date(a.createdAt) : '']));
  const sched = (get_('content/schedule') || {}).weeks || {};
  write_(ss, 'Schedule', ['Shabbat', 'Teacher 1', 'Teacher 1 email', 'Teacher 2', 'Teacher 2 email', 'On hold', 'Note'],
    Object.keys(sched).sort().map(d => { const w = sched[d] || {}; const t1 = w.t1 || {}, t2 = w.t2 || {};
      return [d, t1.name || '', t1.email || '', t2.name || '', t2.email || '', w.onHold ? 'yes' : 'no', w.note || '']; }));
  const settings = get_('content/settings') || {};
  write_(ss, 'Settings', ['Key', 'Value'], Object.keys(settings).map(k => [k, String(settings[k])]));
  const quizzes = list_('quizzes');
  const acts = list_('activity');
  write_(ss, 'Activity', ['Name', 'Email', 'Visits', 'Last visit', 'Days active', 'Portions read', 'Quizzes taken', 'Children'],
    acts.map(a => [a.name || '', a.email || '', a.visits || 0, a.lastVisit ? new Date(a.lastVisit) : '', Object.keys(a.days || {}).length,
      Object.keys(a.read || {}).filter(k => a.read[k]).length, Object.keys(a.quiz || {}).length, (a.children || []).length]));
  const fb = list_('feedback');
  write_(ss, 'Feedback', ['When', 'From', 'Status', 'Feedback'],
    fb.sort((x, y) => (y.at || 0) - (x.at || 0)).map(f => [f.at ? new Date(f.at) : '', f.from || '', f.status || 'new', f.text || '']));
  write_(ss, 'Quizzes', ['Shabbat', 'Portion', 'Quiz (JSON)'], quizzes.map(q => { const id = q._id; delete q._id; return [id, q.portion || '', JSON.stringify(q)]; }));
}
function write_(ss, name, header, rows) {
  const sh = ss.getSheetByName(name) || ss.insertSheet(name);
  sh.clearContents();
  sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight('bold');
  if (rows.length) sh.getRange(2, 1, rows.length, header.length).setValues(rows);
}
