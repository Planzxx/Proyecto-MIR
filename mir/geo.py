"""Provincia y comunidad autónoma de cada localidad del listado."""

_REGIONES = {}


def _add(comunidad: str, provincia: str, localidades: str) -> None:
    for loc in localidades.split("|"):
        _REGIONES[loc.strip()] = (provincia, comunidad)


_add("Andalucía", "Almería", "ALMERÍA|EL EJIDO")
_add("Andalucía", "Cádiz", "CÁDIZ|ALGECIRAS|JEREZ DE LA FRONTERA|LA LÍNEA DE LA CONCEPCIÓN|PUERTO REAL")
_add("Andalucía", "Córdoba", "CÓRDOBA|CABRA")
_add("Andalucía", "Granada", "GRANADA|BAZA|MOTRIL")
_add("Andalucía", "Huelva", "HUELVA")
_add("Andalucía", "Jaén", "JAÉN|LINARES|ÚBEDA")
_add("Andalucía", "Málaga", "MÁLAGA|ANTEQUERA|MARBELLA|RONDA|VÉLEZ-MÁLAGA")
_add("Andalucía", "Sevilla", "SEVILLA|BORMUJOS|OSUNA")
_add("Aragón", "Huesca", "HUESCA")
_add("Aragón", "Teruel", "TERUEL")
_add("Aragón", "Zaragoza", "ZARAGOZA")
_add("Asturias", "Asturias", "AVILÉS|GIJÓN|MIERES|OVIEDO")
_add("Illes Balears", "Illes Balears", "MANACOR|PALMA DE MALLORCA")
_add("Canarias", "Las Palmas", "ARRECIFE|LAS PALMAS DE GRAN CANARIA")
_add("Canarias", "Santa Cruz de Tenerife", "SAN CRISTÓBAL DE LA LAGUNA|SANTA CRUZ DE TENERIFE")
_add("Cantabria", "Cantabria", "SANTANDER|TORRELAVEGA")
_add("Castilla-La Mancha", "Albacete", "ALBACETE")
_add("Castilla-La Mancha", "Ciudad Real", "ALCÁZAR DE SAN JUAN|CIUDAD REAL")
_add("Castilla-La Mancha", "Cuenca", "CUENCA")
_add("Castilla-La Mancha", "Guadalajara", "GUADALAJARA")
_add("Castilla-La Mancha", "Toledo", "TALAVERA DE LA REINA|TOLEDO")
_add("Castilla y León", "Ávila", "ÁVILA")
_add("Castilla y León", "Burgos", "BURGOS")
_add("Castilla y León", "León", "LEÓN|PONFERRADA")
_add("Castilla y León", "Palencia", "PALENCIA")
_add("Castilla y León", "Salamanca", "SALAMANCA")
_add("Castilla y León", "Segovia", "SEGOVIA")
_add("Castilla y León", "Soria", "SORIA")
_add("Castilla y León", "Valladolid", "VALLADOLID")
_add("Castilla y León", "Zamora", "ZAMORA")
_add("Cataluña", "Barcelona", "BADALONA|BARCELONA|CORNELLÀ DE LLOBREGAT|ESPLUGUES DE LLOBREGAT|GRANOLLERS|HOSPITALET DE LLOBREGAT|IGUALADA|MANRESA|MATARÓ|MOLLET DEL VALLÈS|SABADELL|SAN BOI DE LLOBREGAT|SANT BOI DE LLOBREGAT|SANT CUGAT DEL VALLÈS|SANTA COLOMA DE GRAMANET|TERRASSA|VIC|VILANOVA I LA GELTRÚ")
_add("Cataluña", "Girona", "FIGUERES|GIRONA|PALAMÓS|SALT")
_add("Cataluña", "Lleida", "LLEIDA")
_add("Cataluña", "Tarragona", "REUS|TARRAGONA|TORTOSA")
_add("Extremadura", "Badajoz", "BADAJOZ|DON BENITO|MÉRIDA")
_add("Extremadura", "Cáceres", "CÁCERES|PLASENCIA")
_add("Galicia", "A Coruña", "A CORUÑA|FERROL|SANTIAGO DE COMPOSTELA")
_add("Galicia", "Lugo", "LUGO")
_add("Galicia", "Ourense", "OURENSE")
_add("Galicia", "Pontevedra", "PONTEVEDRA|VIGO|VILAGARCÍA DE AROUSA")
_add("La Rioja", "La Rioja", "LOGROÑO")
_add("Madrid", "Madrid", "ALCALÁ DE HENARES|ALCORCÓN|COLLADO VILLALBA|COSLADA|FUENLABRADA|GETAFE|LEGANÉS|MADRID|MAJADAHONDA|MÓSTOLES|PARLA|POZUELO DE ALARCÓN|SAN SEBASTIÁN DE LOS REYES|TORREJÓN DE ARDOZ|VALDEMORO")
_add("Murcia", "Murcia", "CARTAGENA|CIEZA|LORCA|MURCIA|SAN JAVIER")
_add("Navarra", "Navarra", "PAMPLONA|PAMPLONA/ESTELLA")
_add("País Vasco", "Bizkaia", "BARAKALDO|BILBAO|GALDAKAO|ZAMUDIO")
_add("País Vasco", "Gipuzkoa", "DONOSTIA-SAN SEBASTIÁN|SAN SEBASTIÁN")
_add("País Vasco", "Álava", "VITORIA-GASTEIZ")
_add("C. Valenciana", "Alicante", "ALCOY|ALICANTE|DENIA|ELCHE|ELDA|ORIHUELA|SANT JOAN D'ALACANT|TORREVIEJA|VILLAJOYOSA")
_add("C. Valenciana", "Castellón", "CASTELLÓN|VILA-REAL")
_add("C. Valenciana", "Valencia", "ALZIRA|GANDÍA|MANISES|SAGUNTO|VALENCIA|XÁTIVA")
_add("Melilla", "Melilla", "MELILLA")


def region(localidad: str) -> tuple[str, str]:
    """Devuelve (provincia, comunidad) para una localidad en mayúsculas."""
    try:
        return _REGIONES[localidad]
    except KeyError:
        raise KeyError(f"Localidad sin provincia asignada: {localidad!r}") from None
