(() => {
  document.addEventListener('click', async (e) => {
    const card = e.target.closest('.card');
    if (!card) return;

    const heading = card.querySelector('h3');
    if (!heading) return;

    const name = heading.textContent.trim();
    const old = document.getElementById('elassal-tools-panel');
    if (old) old.remove();

    const panel = document.createElement('section');
    panel.id = 'elassal-tools-panel';
    panel.dir = 'rtl';
    panel.style.cssText = 'margin:16px;padding:18px;border:1px solid #20c997;border-radius:12px;background:#111;color:white;line-height:2';

    if (name === 'مبادئ الشبكات') {
      panel.innerHTML = `
        <h3>معمل الشبكات</h3>
        <input id="elassal-target" value="example.com" style="padding:10px;width:90%">
        <p><button id="elassal-dns">اختبار DNS</button>
        <button id="elassal-ping">اختبار Ping</button></p>
        <pre id="elassal-result" dir="ltr" style="white-space:pre-wrap;overflow-wrap:anywhere"></pre>`;
    } else if (name === 'الأمان الدفاعي') {
      panel.innerHTML = `
        <h3>قائمة الأمان الدفاعي</h3>
        <label><input type="checkbox"> تفعيل المصادقة الثنائية</label><br>
        <label><input type="checkbox"> تحديث النظام والتطبيقات</label><br>
        <label><input type="checkbox"> استخدام كلمات مرور قوية وفريدة</label><br>
        <label><input type="checkbox"> مراجعة صلاحيات التطبيقات</label><br>
        <label><input type="checkbox"> عمل نسخة احتياطية</label>`;
    } else if (name === 'سجل التدريب') {
      panel.innerHTML = `
        <h3>سجل التدريب</h3>
        <textarea id="elassal-notes" rows="5" placeholder="اكتب ملاحظاتك..." style="width:95%;padding:10px"></textarea><br>
        <button id="elassal-save">حفظ الملاحظات</button>
        <p id="elassal-status"></p>`;
    } else {
      return;
    }

    card.insertAdjacentElement('afterend', panel);

    if (name === 'سجل التدريب') {
      const notes = panel.querySelector('#elassal-notes');
      try { notes.value = localStorage.getItem('elassal-notes') || ''; } catch {}
      panel.querySelector('#elassal-save').onclick = () => {
        try {
          localStorage.setItem('elassal-notes', notes.value);
          panel.querySelector('#elassal-status').textContent = 'تم حفظ الملاحظات على الجهاز.';
        } catch {
          panel.querySelector('#elassal-status').textContent = 'تعذر الحفظ.';
        }
      };
    }

    for (const action of ['dns', 'ping']) {
      const button = panel.querySelector('#elassal-' + action);
      if (!button) continue;
      button.onclick = async () => {
        const result = panel.querySelector('#elassal-result');
        const target = panel.querySelector('#elassal-target').value.trim();
        result.textContent = 'جاري الاختبار...';
        try {
          const response = await fetch('/api/network-lab', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action, target})
          });
          result.textContent = JSON.stringify(await response.json(), null, 2);
        } catch {
          result.textContent = 'تعذر الاتصال بالخادم.';
        }
      };
    }

    panel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  }, true);
})();
