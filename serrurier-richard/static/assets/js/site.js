/* ==========================================================================
   Scripts du site — volontairement minimalistes (aucune dépendance externe).
   ========================================================================== */
(function () {
  'use strict';

  /* --- Menu mobile -------------------------------------------------------- */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('nav-principal');

  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var ouvert = nav.getAttribute('data-ouvert') === 'true';
      nav.setAttribute('data-ouvert', String(!ouvert));
      toggle.setAttribute('aria-expanded', String(!ouvert));
      toggle.querySelector('.visually-hidden').textContent =
        ouvert ? 'Ouvrir le menu' : 'Fermer le menu';
    });
  }

  /* --- Année du copyright ------------------------------------------------- */
  var annee = document.getElementById('annee');
  if (annee) { annee.textContent = String(new Date().getFullYear()); }

  /* --- Consentement cookies et chargement de Google Analytics -------------
     La CNIL impose un consentement préalable pour les cookies de mesure
     d'audience Google Analytics. Aucun script tiers n'est chargé tant que le
     visiteur n'a pas accepté explicitement.
     ------------------------------------------------------------------------ */

  var GA_ID = document.documentElement.getAttribute('data-ga') || '';
  var CLE = 'consentement-mesure-audience';

  function chargerAnalytics() {
    if (!GA_ID || window.__gaCharge) { return; }
    window.__gaCharge = true;

    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID);
    document.head.appendChild(s);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { anonymize_ip: true });
  }

  function memoriser(valeur) {
    try { localStorage.setItem(CLE, valeur); } catch (e) { /* stockage indisponible */ }
  }

  function lireChoix() {
    try { return localStorage.getItem(CLE); } catch (e) { return null; }
  }

  var choix = lireChoix();

  if (choix === 'accepte') {
    chargerAnalytics();
  } else if (choix !== 'refuse' && GA_ID) {
    afficherBandeau();
  }

  function afficherBandeau() {
    var bandeau = document.createElement('div');
    bandeau.className = 'cookie-bandeau';
    bandeau.setAttribute('role', 'dialog');
    bandeau.setAttribute('aria-label', 'Consentement aux cookies de mesure d’audience');
    bandeau.innerHTML =
      '<div class="cookie-inner">' +
        '<p>Nous utilisons un outil de mesure d’audience pour comprendre comment le site est consulté. ' +
        'Ces cookies ne sont déposés qu’avec votre accord et ne servent pas à de la publicité. ' +
        '<a href="/politique-de-confidentialite">En savoir plus</a></p>' +
        '<div class="cookie-actions">' +
          '<button type="button" class="btn btn-ghost" data-action="refuser">Refuser</button>' +
          '<button type="button" class="btn btn-call" data-action="accepter">Accepter</button>' +
        '</div>' +
      '</div>';

    document.body.appendChild(bandeau);

    bandeau.addEventListener('click', function (e) {
      var action = e.target.getAttribute('data-action');
      if (!action) { return; }
      if (action === 'accepter') {
        memoriser('accepte');
        chargerAnalytics();
      } else {
        memoriser('refuse');
      }
      bandeau.remove();
    });
  }
})();
