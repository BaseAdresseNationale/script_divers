import json
import csv
import sys
from pyproj import Proj, transform
import progressbar


def export(
    chemin, dep, doc_municipality, doc_postcode, doc_group, doc_housenumber, doc_position
):
    '''
    Usage : export <chemin json initial> <departement>
    Exemple : export . 01
    Remarque : le json ban v0 est genere a l'emplacement des json
    '''
    municipalities = {}
    postcodes = {}
    groups = {}
    housenumbers = {}
    housenumbers_id = {}
    positions = {}
    exportPath = '{}/export_{}.csv'.format(chemin, dep)
    c = csv.writer(
                open(exportPath, 'w'),
                delimiter=',',
                lineterminator='\n'
    )
    c.writerow(['id', 'nom_voie', 'id_fantoir', 'numero', 'rep', 'code_insee',
                'code_post', 'alias', 'nom_ld', 'libelle_acheminement',
                'x', 'y', 'lon', 'lat', 'nom_commune'])

    with open(chemin+'/'+doc_municipality, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['insee'].startswith(dep):
                municipalities[data['id']] = data
    print('{} municipalities'.format(len(municipalities)))

    with open(chemin+'/'+doc_postcode, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['municipality'] in municipalities.keys():
                postcodes[data['id']] = data
    print('{} postcodes'.format(len(postcodes)))

    with open(chemin+'/'+doc_group, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['municipality'] in municipalities.keys():
                groups[data['id']] = data
    print('{} groups'.format(len(groups)))

    housenumberNb = 0
    with open(chemin+'/'+doc_housenumber, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['parent'] in groups.keys():
                housenumbers.setdefault(data['parent'], []).append(data)
                housenumbers_id[data['id']] = None
                housenumberNb += 1
    print('{} housenumbers'.format(housenumberNb))

    positionNb = 0
    with open(chemin+'/'+doc_position, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['housenumber'] in housenumbers_id.keys():
                positionNb += 1
                positions.setdefault(data['housenumber'], []).append(data)
    print('{} positions'.format(positionNb))
    print('{} positions regroupees par hn'.format(len(positions)))


    epsg_code = getEPSGCode(dep)

    count = 0
    bar = progressbar.ProgressBar(maxval=len(groups))
    bar.start()
    for group in groups.values():
        count += 1
        bar.update(count)
        group_hns = housenumbers.get(group['id'], [])
        municipality = municipalities.get(group['municipality'], None)
        for housenumber in group_hns:
            position = findPosition(housenumber, positions)
            ancestors = findAncestors(housenumber, groups)
            postcode = postcodes.get(housenumber['postcode'], None)

            writeNewLine(c, housenumber, group, ancestors, municipality, postcode, position, epsg_code)
    bar.finish()

def writeNewLine(writer, housenumber, group, ancestors, municipality, postcode, position, epsg_code):
    # ecrit une nouvelle ligne dans le fichier d export csv
    groupResult = compulseGroups(group, ancestors)
    if position is None:
        lonlat = ('', '')
    else:
        lonlat = (
            position["center"]["coordinates"][0],
            position["center"]["coordinates"][1])
    positionXY = convertPosition(position, epsg_code)

    writer.writerow([housenumber['id'],
                    groupResult[0],
                    group['fantoir'],
                    housenumber['number'],
                    housenumber['ordinal'],
                    municipality['insee'] if municipality is not None else '',
                    postcode['code'] if postcode is not None else '',
                    group['alias'],
                    groupResult[1],
                    postcode['name'] if postcode is not None else '',
                    positionXY[0],
                    positionXY[1],
                    lonlat[0],
                    lonlat[1],
                    municipality['name'] if municipality is not None else ''])


def convertPosition(position, code):
    # pour une position donnee retourne les coordonnees projetees
    # selon la projection native
    # return (x,y)
    positionXY = ('', '')
    if position is None:
        return positionXY
    inProj = Proj(init='epsg:4326')
    outProj = Proj(init=code)
    positionXY = transform(
                            inProj,
                            outProj,
                            position["center"]["coordinates"][0],
                            position["center"]["coordinates"][1])
    return positionXY


def getEPSGCode(dep):
    # renvoie le code epsg correspondant pour un departement donne
    codes = {
        '971': '4559',
        '972': '4559',
        '973': '2972',
        '974': '2975',
        '975': '4467',
        '976': '4471'
    }
    code = codes.get(dep, '2154')
    return 'epsg:{}'.format(code)


def compulseGroups(group, ancestors):
    # return (nom_voie, nom_ld)
    result = ['', '']

    if group["kind"] == 'way':
        ancestor = findBestAncestor(ancestors, 'area')
        result[0] = group["name"]
        if ancestor is not None:
            result[1] = ancestor["name"]
    elif group["kind"] == 'area':
        ancestor = findBestAncestor(ancestors, 'way')
        result[1] = group["name"]
        if ancestor is None:
            result[0] = group["name"]
        else:
            result[0] = ancestor["name"]
    return result


def findBestAncestor(ancestors, type):
    # selectionne l ancestor le plus recent d un type donne
    # parmi un tableau d ancestors
    best_ancestor = None
    for ancestor in ancestors:
        if ancestor["kind"] == type and best_ancestor is None:
            best_ancestor = ancestor
        elif ancestor["kind"] == type and ancestor['modified_at'] > best_ancestor['modified_at']:
            best_ancestor = ancestor
    return best_ancestor


def findPosition(housenumber, positions):
    # selectionne la position la plus recente
    # pour le meilleur kind disponible
    hn_positions = positions.get(housenumber['id'], [])
    kinds = [
            "entrance", "building", "staircase", "unit",
            "parcel", "segment", "utility", "area", "postal", "unknown"]
    ids = {}
    bestPosition = None
    for position in hn_positions:
        ids.setdefault(position['kind'], []).append(position)
    for kind in kinds:
        if kind in ids.keys():
            bestPosition = ids[kind][0]
            for position in ids[kind]:
                if position['modified_at'] > bestPosition['modified_at']:
                    bestPosition = position
            break
    return bestPosition


def findAncestors(housenumber, groups):
    # renvoie le tableau d ancestors lie a un housenumber donne
    results = []
    anc_ids = housenumber["ancestors"]
    if anc_ids:
        for anc_id in anc_ids:
            results.append(groups.get(anc_id))
    return results


if __name__ == "__main__":
    municipalityFile = sys.argv[3] if len(sys.argv) > 3 else "municipality.ndjson"
    postcodeFile = sys.argv[4] if len(sys.argv) > 4 else "postcode.ndjson"
    groupFile = sys.argv[5] if len(sys.argv) > 5 else "group.ndjson"
    housenumberFile = sys.argv[6] if len(sys.argv) > 6 else "housenumber.ndjson"
    positionFile = sys.argv[7] if len(sys.argv) > 7 else "position.ndjson"
    comment = '''
    Usage : export <chemin json initial> <departement>
    Exemple : export . 01
    Remarque : le json ban v0 est genere a l'emplacement des json
    '''
    try:
        chemin = sys.argv[1]
        dep = sys.argv[2]
    except:
        print (comment)
        sys.exit()
    export(chemin, dep, municipalityFile, postcodeFile, groupFile, housenumberFile, positionFile)
