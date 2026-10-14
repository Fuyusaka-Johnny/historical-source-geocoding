/* Text from documents and models is rendered as text, never as HTML. */
let current = null;
const $ = id => document.getElementById(id);
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
async function request(url, options) {
  const response = await fetch(url, options);
  let data;
  try { data = await response.json(); } catch { throw new Error('服务返回异常，请检查后台状态'); }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '输入内容或服务配置有误');
  return data;
}
function show(data) {
  current = data;
  current.manual_selections = [];
  $('results').replaceChildren();
  $('export').disabled = false;
  const failures = (data.failures || []).length;
  $('status').textContent = data.demo ? data.notice :
    `已返回 ${data.records.length} 条记录；分块 ${data.segment_count} 段；失败 ${failures} 段。` +
    (data.matching_status === 'failed' ? ` ${data.matching_message}` : ' 地点候选均待人工核验。');
  if (!data.records.length && !failures) $('status').textContent += ' 未提取到记录，不代表史料中没有相关信息。';
  (data.failures || []).forEach(failure => $('results').append(node('p', `第 ${failure.segment_index} 段：${failure.message}`, 'warning')));
  data.records.forEach((record, index) => {
    const card = node('article', undefined, 'record');
    card.append(node('h3', `${index + 1} · ${record.day || '日期未明'}`));
    card.append(node('p', record.original_text, 'original'));
    card.append(node('div', '人物与行为', 'label'));
    card.append(node('p', record.people.map(p => `${p.name}：${p.action}`).join('；') || '未提取'));
    card.append(node('div', '事件', 'label'));
    const events = node('ul');
    record.events.forEach(event => events.append(node('li', event)));
    card.append(events);
    (record.location_matches || []).forEach((group, groupIndex) => {
      card.append(node('div', `地点表达：${group.query}`, 'label'));
      if (!group.candidates.length) card.append(node('p', '无名称或别名匹配，保留待查。', 'warning'));
      if (group.truncated) card.append(node('p', '候选超过显示上限（50 条），当前列表不完整。', 'warning'));
      const groupBox = node('div');
      const choices = [{id:null, name:'暂不选择'}, ...group.candidates];
      choices.forEach(candidate => {
        const box = node('div', undefined, 'candidate');
        const label = node('label');
        const radio = node('input');
        radio.type = 'radio'; radio.name = `choice-${index}-${groupIndex}`;
        radio.checked = candidate.id === null;
        radio.addEventListener('change', () => {
          current.manual_selections = current.manual_selections.filter(s => !(s.record_index === index && s.query === group.query));
          if (candidate.id !== null) current.manual_selections.push({record_index:index,query:group.query,
            selected_place_id:candidate.id,candidate:{...candidate},status:'manual_selection_for_review'});
        });
        label.append(radio, document.createTextNode(candidate.id === null ? candidate.name : `${candidate.name} · ID ${candidate.id}`));
        box.append(label);
        if (candidate.id !== null) {
          box.append(node('div', candidate.lat == null || candidate.lng == null ? '坐标缺失' : `纬度 ${candidate.lat} / 经度 ${candidate.lng}`));
          box.append(node('div', `出处：${candidate.source} ${candidate.source_detail || ''}`));
          if (candidate.shape_code === 2) box.append(node('div', '线要素；显示坐标仅为端点，不能视为事件发生点。', 'warning'));
          if (candidate.notes) box.append(node('div', candidate.notes));
        }
        groupBox.append(box);
      });
      card.append(groupBox);
    });
    $('results').append(card);
  });
}
async function busy(button, action) {
  button.disabled = true;
  try { await action(); } catch(error) { $('status').textContent = error.message; }
  finally { button.disabled = false; }
}
$('demo').addEventListener('click', () => busy($('demo'), async () => {
  const result = await request('/api/demo'); $('source').value = result.input_text; show(result);
}));
$('extract').addEventListener('click', () => busy($('extract'), async () => {
  const text = $('source').value;
  if (!text.trim()) throw new Error('请先输入史料正文');
  if (text.startsWith('【人工编写演示句')) throw new Error('当前为固定演示文本，请用“查看人工演示”；真实抽取请换成你的史料。');
  $('status').textContent = '正在抽取并查询，较长文本可能需要等待……';
  show(await request('/api/extract', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}));
}));
$('lookup').addEventListener('submit', async event => {
  event.preventDefault();
  try { $('lookup-result').textContent = JSON.stringify(await request(`/api/geocode?name=${encodeURIComponent($('place').value)}`), null, 2); }
  catch(error) { $('lookup-result').textContent = error.message; }
});
$('export').addEventListener('click', () => {
  if (!current) return;
  const blob = new Blob([JSON.stringify(current, null, 2)], {type:'application/json;charset=utf-8'});
  const url = URL.createObjectURL(blob); const link = node('a');
  link.href = url; link.download = current.demo ? 'synthetic-demo-review.json' : 'historical-source-review.json';
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
