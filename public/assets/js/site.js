/* ==========================================================================
   Serrurier Richard — scripts du site.

   Aucune dépendance, aucun framework, aucune requête réseau au chargement.
   Le fichier reste sous 5 Ko afin de ne pas peser sur le temps d'affichage.

   Trois responsabilités, et rien d'autre :
     1. le menu mobile ;
     2. le consentement aux cookies de mesure d'audience ;
     3. le suivi des conversions, uniquement après consentement.

   Tout le site fonctionne sans JavaScript : navigation, formulaire de devis,
   liens d'appel. Ce fichier n'ajoute que du confort et de la mesure.
   ========================================================================== */
(function () {
  'use strict';

  var racine = document.documentElement;

  /* --- 1. Menu mobile ----------------------------------------------------- */

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

    // Échap referme le menu : sans cela, le focus reste piégé au clavier.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.getAttribute('data-ouvert') === 'true') {
        toggle.click();
        toggle.focus();
      }
    });
  }

  /* --- 2. Année du copyright ---------------------------------------------- */

  var annee = document.getElementById('annee');
  if (annee) { annee.textContent = String(new Date().getFullYear()); }

  /* --- 3. Consentement et mesure d'audience -------------------------------
     La CNIL impose un consentement préalable pour les cookies de mesure
     d'audience Google. Aucun script tiers n'est chargé, et aucun événement
     n'est transmis, tant que le visiteur n'a pas accepté explicitement.

     Les identifiants viennent de src/config.sh (GA4_ID, GTM_ID) et sont
     déposés sur la balise <html> au build. Vides, tout ce bloc est inerte.
     ------------------------------------------------------------------------ */

  var GA_ID  = racine.getAttribute('data-ga')  || '';
  var GTM_ID = racine.getAttribute('data-gtm') || '';
  var MESURE_ACTIVE = Boolean(GA_ID || GTM_ID);
  var CLE = 'consentement-mesure-audience';

  var consentement = false;
  var fileAttente = [];   // événements survenus avant la réponse au bandeau

  function memoriser(valeur) {
    try { localStorage.setItem(CLE, valeur); } catch (e) { /* stockage indisponible */ }
  }

  function lireChoix() {
    try { return localStorage.getItem(CLE); } catch (e) { return null; }
  }

  function chargerMesure() {
    if (window.__mesureChargee) { return; }
    window.__mesureChargee = true;

    window.dataLayer = window.dataLayer || [];

    if (GTM_ID) {
      window.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });
      injecter('https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(GTM_ID));
    }

    if (GA_ID) {
      injecter('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID));
      window.gtag = function () { window.dataLayer.push(arguments); };
      window.gtag('js', new Date());
      window.gtag('config', GA_ID, { anonymize_ip: true });
    }
  }

  function injecter(src) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    document.head.appendChild(s);
  }

  /* Envoi d'un événement de conversion.
     Avant consentement, l'événement est mis de côté : s'il accepte ensuite,
     la conversion n'est pas perdue ; s'il refuse, la file est vidée sans
     jamais rien émettre. */
  function suivre(nom, parametres) {
    if (!MESURE_ACTIVE) { return; }
    if (!consentement) {
      if (fileAttente.length < 20) { fileAttente.push([nom, parametres]); }
      return;
    }
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event: nom }, parametres || {}));
    if (typeof window.gtag === 'function') {
      window.gtag('event', nom, parametres || {});
    }
  }

  function accepter() {
    consentement = true;
    chargerMesure();
    fileAttente.forEach(function (e) { suivre(e[0], e[1]); });
    fileAttente = [];
  }

  var choix = lireChoix();
  if (choix === 'accepte') {
    accepter();
  } else if (choix !== 'refuse' && MESURE_ACTIVE) {
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
        '<a href="/politique-confidentialite">En savoir plus</a></p>' +
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
        accepter();
      } else {
        memoriser('refuse');
        fileAttente = [];
      }
      bandeau.remove();
    });
  }

  /* --- 4. Suivi des conversions -------------------------------------------
     Les éléments porteurs de data-track sont suivis sans code spécifique par
     page. La zone (en-tête, héros, barre mobile…) permet de savoir QUEL appel
     à l'action convertit, information décisive pour arbitrer la mise en page.
     ------------------------------------------------------------------------ */

  document.addEventListener('click', function (e) {
    var cible = e.target.closest('[data-track]');
    if (!cible) { return; }
    suivre(cible.getAttribute('data-track'), {
      zone: cible.getAttribute('data-track-zone') || 'inconnue',
      page: location.pathname
    });
  });

  // Les liens d'appel et de courriel sont suivis même sans data-track :
  // ce sont les deux conversions principales du site.
  document.addEventListener('click', function (e) {
    var lien = e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!lien || lien.hasAttribute('data-track')) { return; }
    suivre(lien.getAttribute('href').indexOf('tel:') === 0 ? 'appel' : 'clic_email', {
      zone: 'lien-texte',
      page: location.pathname
    });
  });

  // Conversion « devis envoyé » : signalée par la page de remerciement, donc
  // uniquement lorsque le serveur a réellement accepté et transmis la demande.
  if (document.body.getAttribute('data-conversion')) {
    suivre(document.body.getAttribute('data-conversion'), { page: location.pathname });
  }

  /* --- 5. Apparition au défilement -----------------------------------------
     Les éléments portant la classe « apparait » se révèlent quand ils entrent
     dans le champ. Sans JavaScript ils restent simplement visibles : la
     classe « visible » n'est jamais posée, mais la règle CSS correspondante
     n'est pas non plus appliquée puisque le sélecteur exige les deux classes.
     Un visiteur ayant demandé moins d'animations est servi directement.
     ------------------------------------------------------------------------ */

  var elements = document.querySelectorAll('.apparait');

  if (elements.length) {
    var moinsAnime = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (moinsAnime || !('IntersectionObserver' in window)) {
      elements.forEach(function (el) { el.classList.add('visible'); });
    } else {
      var vigie = new IntersectionObserver(function (entrees) {
        entrees.forEach(function (entree, i) {
          if (!entree.isIntersecting) { return; }
          // Léger décalage entre voisins : la grille se compose au lieu
          // d'apparaître d'un bloc.
          setTimeout(function () { entree.target.classList.add('visible'); }, i * 70);
          vigie.unobserve(entree.target);
        });
      }, { rootMargin: '0px 0px -80px 0px', threshold: 0.08 });

      elements.forEach(function (el) { vigie.observe(el); });
    }
  }

  /* --- 6. Galerie : agrandissement au clic ---------------------------------
     Une visionneuse minimale, sans dépendance. Fermeture au clic, à la touche
     Échap, et retour du focus sur l'image d'origine.
     ------------------------------------------------------------------------ */

  var galerie = document.querySelector('.galerie');

  if (galerie) {
    galerie.querySelectorAll('figure').forEach(function (figure) {
      var image = figure.querySelector('img');
      if (!image) { return; }
      figure.setAttribute('tabindex', '0');
      figure.setAttribute('role', 'button');
      figure.setAttribute('aria-label', 'Agrandir : ' + image.alt);
      figure.style.cursor = 'zoom-in';

      function ouvrir() { agrandir(image, figure); }
      figure.addEventListener('click', ouvrir);
      figure.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); ouvrir(); }
      });
    });
  }

  function agrandir(image, origine) {
    var voile = document.createElement('div');
    voile.className = 'visionneuse';
    voile.setAttribute('role', 'dialog');
    voile.setAttribute('aria-modal', 'true');
    voile.setAttribute('aria-label', image.alt);
    voile.innerHTML =
      '<button type="button" class="visionneuse-fermer" aria-label="Fermer">&times;</button>' +
      '<img src="' + image.getAttribute('src') + '" alt="' + image.alt.replace(/"/g, '&quot;') + '">';

    document.body.appendChild(voile);
    document.body.style.overflow = 'hidden';
    voile.querySelector('.visionneuse-fermer').focus();

    function fermer() {
      voile.remove();
      document.body.style.overflow = '';
      document.removeEventListener('keydown', surTouche);
      if (origine) { origine.focus(); }
    }
    function surTouche(e) { if (e.key === 'Escape') { fermer(); } }

    voile.addEventListener('click', fermer);
    document.addEventListener('keydown', surTouche);
  }

  /* --- 5. Formulaire de devis ---------------------------------------------
     Le formulaire est entièrement validé côté serveur : ce bloc n'ajoute que
     le confort d'un message immédiat et l'horodatage anti-robot. Le retirer
     ne casserait rien.
     ------------------------------------------------------------------------ */

  var form = document.querySelector('form[data-devis]');
  if (form) {
    var horodatage = form.querySelector('input[name="_horodatage"]');
    if (horodatage) { horodatage.value = String(Math.floor(Date.now() / 1000)); }

    form.addEventListener('submit', function () {
      var bouton = form.querySelector('button[type="submit"]');
      if (bouton && form.checkValidity()) {
        bouton.disabled = true;
        bouton.textContent = 'Envoi en cours…';
        // Réactivation si l'utilisateur revient en arrière depuis le cache.
        setTimeout(function () {
          bouton.disabled = false;
          bouton.textContent = 'Envoyer ma demande de devis';
        }, 8000);
      }
    });
  }
})();
