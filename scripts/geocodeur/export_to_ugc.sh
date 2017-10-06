#!/bin/sh
# Script d'export de la BAN en fomat pivot pour le geocodage
################################################################################
# ARGUMENT :* $1 : repertoire dans lequel seront generes le fichier txt
#############################################################################
# PGDATABASE = copie de la ban a exporter
#############################################################################

outPath=$1
dep=$2

if [ $# -lt 1 ]; then
    echo "Usage : export_to_ugc.sh <outPath> <dep>"
    echo "Exemple : export_to_ugc.sh . 90"
    exit 1
fi

echo "\set ON_ERROR_STOP 1" > commandeTemp.sql

echo "DROP TABLE IF EXISTS municipality_${dep};" >> commandeTemp.sql
echo "CREATE TABLE municipality_${dep} AS (SELECT pk, name, insee FROM municipality WHERE insee LIKE '${dep}%');" >> commandeTemp.sql
echo "DROP TABLE IF EXISTS postcode_${dep};" >> commandeTemp.sql
echo "CREATE TABLE postcode_${dep} AS (SELECT p.pk, p.code, p.complement, p.municipality_id FROM postcode p, municipality_${dep} m WHERE p.municipality_id=m.pk);" >> commandeTemp.sql
echo "DROP TABLE IF EXISTS group_${dep};" >> commandeTemp.sql
echo "CREATE TABLE group_${dep} AS (SELECT g.pk, g.name, g.municipality_id FROM \"group\" g, municipality_${dep} m WHERE g.municipality_id=m.pk AND g.name IS NOT NULL);" >> commandeTemp.sql
echo "DROP TABLE IF EXISTS housenumber_${dep};" >> commandeTemp.sql
echo "CREATE TABLE housenumber_${dep} AS (SELECT h.pk, h.number, h.ordinal, h.parent_id FROM housenumber h, group_${dep} g WHERE h.parent_id=g.pk AND h.number IS NOT NULL);" >> commandeTemp.sql
echo "UPDATE housenumber_${dep} SET ordinal='' WHERE ordinal is null;" >> commandeTemp.sql
echo "DROP TABLE IF EXISTS position_${dep};" >> commandeTemp.sql
echo "CREATE TABLE position_${dep} AS 
(SELECT st_x(p.center) as X, st_y(p.center) as Y, p.housenumber_id  FROM position p, housenumber_${dep} h WHERE p.housenumber_id=h.pk and st_x(p.center)=
(select min(st_x(p2.center)) from position p2 where p2.housenumber_id=h.pk group by p2.housenumber_id));" >> commandeTemp.sql

echo "DROP TABLE IF EXISTS level2point_${dep};" >> commandeTemp.sql
echo "CREATE TABLE level2point_${dep} (streetName text, streetAttribute text, endNumberL text, startNumberL text, endNumberR text, startNumberR text, cityName text, cityAttribute text, cityUniqueId text, X1 text, Y1 text, X2 text, Y2 text, geom text);" >> commandeTemp.sql
echo "INSERT INTO level2point_${dep} (streetName, cityName, cityUniqueId, X2, Y2) SELECT h.number||''||h.ordinal||' '||g.name, m.name, m.insee, p.X, p.Y FROM municipality_${dep} m, group_${dep} g, housenumber_${dep} h, position_${dep} p WHERE p.housenumber_id=h.pk and h.parent_id=g.pk and g.municipality_id=m.pk and g.name is not null and h.number is not null;" >> commandeTemp.sql

echo "\COPY level2point_${dep} TO '${outPath}/level2point_${dep}.txt';" >> commandeTemp.sql

psql -f commandeTemp.sql

if [ $? -ne 0 ]
then
    echo "Erreur lors de l export"
    exit 1
fi

echo "FIN"

