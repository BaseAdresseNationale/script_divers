#### export_ban_v0.py ####
Le script export_ban_v0.py permet de générer les exports en csv ban v0 à partir de l'export json de la banv1.

Nécessite Python 3.x + le package pyproj

#### En entrée: ####
Les fichiers de sortie de l'export BAN au format json

#### En arguments: ####
- arg1: chemin repertoire pour export et fichiers a traiter
- arg2: departement a traiter
- arg3: nom du fichier des municipality. Argument facultatif. Par défaut le fichier doit être municipality.ndjson. 
- arg4: nom du fichier des postcode. Argument facultatif. Par défaut le fichier doit être postcode.ndjson.
- arg5: nom du fichier des group. Argument facultatif. Par défaut le fichier doit être group.ndjson.
- arg6: nom du fichier des housenumber. Argument facultatif. Par défaut le fichier doit être housenumber.ndjson.

Exemple :  python export_ban_v0.py ~/data/ban_prod/export_json 33

#### En sortie: ####
Fichier csv au format ban v0 odbl (sans le champ nom_afnor)

#### remarques sur le traitement effectué: ####
Pour la géometrie projetée, la projection native est utilisée (Lambert93 pour France métropolitaine...)

En cas de positions multiples sur un housenumber est pris par ordre de priorité:
"entrance", "building", "staircase", "unit", "parcel", "segment", "utility", "area", "postal", "unknown"
Puis si plusieurs position du même type, on prend la position la plus récente (champ modified_at)

Pour le remplissage de nom_voie/lieu dit on se base sur le type du group
on complète les noms avec les ancestors. Si deux ancestors de même type on prend le plus récent
S'il reste vide, on remplit le nom de voie avec le nom du lieu dit
