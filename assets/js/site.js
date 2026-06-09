(function () {
	'use strict';

	// --- Form submission handlers (demo — shows success state) ---
	function handleFormSubmit(formId, successId) {
		var form = document.getElementById(formId);
		if (!form) return;
		form.addEventListener('submit', function (e) {
			e.preventDefault();
			if (!form.checkValidity()) {
				form.reportValidity();
				return;
			}
			form.style.display = 'none';
			if (successId) {
				var msg = document.getElementById(successId);
				if (msg) msg.style.display = 'block';
			} else {
				var thanks = document.createElement('p');
				thanks.innerHTML = '<strong>Thanks! Your message has been received. I\'ll be in touch within 24 hours.</strong>';
				thanks.style.textAlign = 'center';
				thanks.style.padding = '2rem 0';
				form.parentNode.insertBefore(thanks, form.nextSibling);
			}
		});
	}

	handleFormSubmit('booking-form', 'booking-success');
	handleFormSubmit('contact-form', null);
	handleFormSubmit('newsletter-form', null);
	handleFormSubmit('blog-newsletter-form', null);

	// --- Gallery filter ---
	var filterBtns = document.querySelectorAll('.filter-btn');
	var galleryItems = document.querySelectorAll('.gallery-item');

	filterBtns.forEach(function (btn) {
		btn.addEventListener('click', function () {
			filterBtns.forEach(function (b) { b.classList.remove('active'); });
			btn.classList.add('active');

			var filter = btn.getAttribute('data-filter');
			galleryItems.forEach(function (item) {
				if (filter === 'all') {
					item.classList.remove('hidden');
				} else {
					var cats = item.getAttribute('data-category') || '';
					if (cats.indexOf(filter) !== -1) {
						item.classList.remove('hidden');
					} else {
						item.classList.add('hidden');
					}
				}
			});
		});
	});

	// --- Set min date for booking date picker to today ---
	var datePicker = document.getElementById('b-date');
	if (datePicker) {
		var today = new Date();
		var yyyy = today.getFullYear();
		var mm = String(today.getMonth() + 1).padStart(2, '0');
		var dd = String(today.getDate()).padStart(2, '0');
		datePicker.min = yyyy + '-' + mm + '-' + dd;
	}

})();
