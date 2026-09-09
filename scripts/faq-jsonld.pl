#!/usr/bin/env perl
# ---------------------------------------------------------------------------
# Produit le bloc JSON-LD FAQPage d'une page, à partir de ses blocs <details>.
#
#   perl scripts/faq-jsonld.pl < corps-de-page.html
#
# Le balisage est ainsi TOUJOURS dérivé du texte réellement affiché : Google
# exige cette correspondance exacte, et la corriger à la main sur dix pages
# finit toujours par produire un écart. Rien à maintenir en double.
#
# Sortie vide s'il n'y a aucun bloc <details> : la page n'aura pas de FAQPage.
# ---------------------------------------------------------------------------
use strict;
use warnings;

my $html = do { local $/; <STDIN> };

# Neutralise les scripts : un JSON-LD déjà présent ne doit pas être relu.
$html =~ s{<script\b.*?</script>}{}gis;

my @entrees;

while ($html =~ m{<details\b[^>]*>(.*?)</details>}gis) {
    my $bloc = $1;

    my ($question) = $bloc =~ m{<summary\b[^>]*>(.*?)</summary>}is;
    next unless defined $question;

    my $reponse = $bloc;
    $reponse =~ s{<summary\b[^>]*>.*?</summary>}{}is;

    push @entrees, [ texte($question), texte($reponse) ];
}

exit 0 unless @entrees;

my @lignes;
for my $e (@entrees) {
    push @lignes,
        '    {' . "\n"
      . '      "@type": "Question",' . "\n"
      . '      "name": "' . $e->[0] . '",' . "\n"
      . '      "acceptedAnswer": { "@type": "Answer", "text": "' . $e->[1] . '" }' . "\n"
      . '    }';
}

print '<script type="application/ld+json">' . "\n";
print '{' . "\n";
print '  "@context": "https://schema.org",' . "\n";
print '  "@type": "FAQPage",' . "\n";
print '  "mainEntity": [' . "\n";
print join(",\n", @lignes), "\n";
print '  ]' . "\n";
print '}' . "\n";
print '</script>' . "\n";

# --- Conversion d'un fragment HTML en littéral JSON ------------------------
sub texte {
    my ($t) = @_;

    # Les balises de bloc deviennent des espaces pour ne pas coller les mots.
    $t =~ s{<(?:br|p|li|div)\b[^>]*>}{ }gi;
    $t =~ s{</(?:p|li|div|h[1-6])>}{ }gi;
    $t =~ s{<[^>]+>}{}g;

    # Entités rencontrées dans le contenu du site.
    my %ent = (
        'amp' => '&', 'lt' => '<', 'gt' => '>', 'quot' => '"', 'apos' => "'",
        'nbsp' => ' ', 'eacute' => 'é', 'egrave' => 'è', 'agrave' => 'à',
        'ccedil' => 'ç', 'ecirc' => 'ê', 'euro' => '€', 'hellip' => '…',
        'laquo' => '«', 'raquo' => '»', 'rsquo' => '’', 'copy' => '©',
    );
    $t =~ s{&([a-zA-Z]+);}{ exists $ent{$1} ? $ent{$1} : "&$1;" }ge;
    $t =~ s{&#(\d+);}{ chr($1) }ge;
    $t =~ s{&#x([0-9a-fA-F]+);}{ chr(hex($1)) }ge;

    $t =~ s{\s+}{ }g;
    $t =~ s{^\s+|\s+$}{}g;

    # Échappement JSON.
    $t =~ s{\\}{\\\\}g;
    $t =~ s{"}{\\"}g;

    return $t;
}
