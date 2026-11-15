
es_un(laptop,      electronica).
es_un(smartphone,  electronica).
es_un(tablet,      electronica).
es_un(television,  electronica).
es_un(camisa,      ropa).
es_un(pantalon,    ropa).
es_un(chaqueta,    ropa).
es_un(zapatos,     ropa).
es_un(silla,       hogar).
es_un(mesa,        hogar).
es_un(lampara,     hogar).
es_un(electronica, producto).
es_un(ropa,        producto).
es_un(hogar,       producto).

es_un(laptop_hp,          laptop).
es_un(laptop_asus,        laptop).
es_un(laptop_dell,        laptop).
es_un(smartphone_sams,    smartphone).
es_un(smartphone_xiaomi,  smartphone).
es_un(smartphone_motorola, smartphone).
es_un(tablet_ipad,        tablet).
es_un(tablet_samsung,     tablet).
es_un(tv_lg,              television).
es_un(tv_sony,            television).
es_un(camisa_polo,        camisa).
es_un(camisa_formal,      camisa).
es_un(pantalon_jean,      pantalon).
es_un(pantalon_cargo,     pantalon).
es_un(chaqueta_cuero,     chaqueta).
es_un(chaqueta_jean,      chaqueta).
es_un(zapatos_deportivos, zapatos).
es_un(zapatos_formales,   zapatos).
es_un(silla_oficina,      silla).
es_un(mesa_comedor,       mesa).
es_un(lampara_led,        lampara).

% instancia/1 marca cada producto final del catalogo (no una
% categoria/subtipo), para poder recorrerlos a todos y verificar
% que cada uno tiene al menos una recomendacion.
instancia(laptop_hp).
instancia(laptop_asus).
instancia(laptop_dell).
instancia(smartphone_sams).
instancia(smartphone_xiaomi).
instancia(smartphone_motorola).
instancia(tablet_ipad).
instancia(tablet_samsung).
instancia(tv_lg).
instancia(tv_sony).
instancia(camisa_polo).
instancia(camisa_formal).
instancia(pantalon_jean).
instancia(pantalon_cargo).
instancia(chaqueta_cuero).
instancia(chaqueta_jean).
instancia(zapatos_deportivos).
instancia(zapatos_formales).
instancia(silla_oficina).
instancia(mesa_comedor).
instancia(lampara_led).

propiedad(producto,    tiene_precio).
propiedad(electronica, requiere_electricidad).
propiedad(laptop,      portatil).
propiedad(smartphone,  portatil).
propiedad(tablet,      portatil).
propiedad(ropa,        textil).
propiedad(hogar,       mobiliario).


compatible(laptop,     mouse).
compatible(laptop,     funda_laptop).
compatible(laptop,     audifonos).
compatible(smartphone, funda_smartphone).
compatible(smartphone, cargador_rapido).
compatible(smartphone, audifonos).
compatible(tablet,     funda_tablet).
compatible(tablet,     teclado_bluetooth).
compatible(television, soporte_pared).
compatible(television, control_remoto).
compatible(camisa,     corbata).
compatible(pantalon,   cinturon).
compatible(chaqueta,   bufanda).
compatible(zapatos,    plantillas).
compatible(silla,      cojin).
compatible(mesa,       mantel).
compatible(lampara,    bombilla_led).
compatible(lampara,    cable_extension).



es_un_transitivo(X, Y) :-
    es_un(X, Y).

es_un_transitivo(X, Y) :-
    es_un(X, Z),
    es_un_transitivo(Z, Y).


tiene_propiedad(X, P) :-
    propiedad(X, P).
tiene_propiedad(X, P) :-
    es_un(X, Y),
    tiene_propiedad(Y, P).

recomendar_accesorio(X, A) :-
    compatible(X, A).
recomendar_accesorio(X, A) :-
    es_un_transitivo(X, Categoria),
    compatible(Categoria, A).

main :-
    write('=== HERENCIA TRANSITIVA DE laptop_hp ==='), nl,
    forall(
        es_un_transitivo(laptop_hp, Categoria),
        (write(' - laptop_hp es un '), write(Categoria), nl)
    ),

    write('=== PROPIEDADES HEREDADAS DE laptop_hp ==='), nl,
    forall(
        tiene_propiedad(laptop_hp, Prop),
        (write(' - laptop_hp tiene propiedad '), write(Prop), nl)
    ),

    write('=== ACCESORIOS RECOMENDADOS PARA laptop_hp ==='), nl,
    forall(
        recomendar_accesorio(laptop_hp, Accesorio),
        (write(' - Se recomienda: '), write(Accesorio), nl)
    ),

    write('=== ACCESORIOS RECOMENDADOS PARA smartphone_xiaomi ==='), nl,
    forall(
        recomendar_accesorio(smartphone_xiaomi, Accesorio2),
        (write(' - Se recomienda: '), write(Accesorio2), nl)
    ),

    write('=== ACCESORIOS RECOMENDADOS PARA silla_oficina ==='), nl,
    forall(
        recomendar_accesorio(silla_oficina, Accesorio3),
        (write(' - Se recomienda: '), write(Accesorio3), nl)
    ),

    write('=== VERIFICACION: RECOMENDACIONES PARA TODO EL CATALOGO ==='), nl,
    forall(
        instancia(Producto),
        (
            findall(A, recomendar_accesorio(Producto, A), Accesorios),
            write(' - '), write(Producto), write(' -> '), write(Accesorios), nl
        )
    ).

% ------------------------------------------------------------
% CONSULTA PARAMETRIZADA PARA INTEGRACION CON PYTHON
% ------------------------------------------------------------
% A diferencia de main/0 (demo fija con 3 productos), consultar/1
% imprime el mismo tipo de informacion para UN solo producto dado
% como parametro, en lineas "ETIQUETA:valor" faciles de parsear
% desde Python con str.partition(':').
consultar(Producto) :-
    write('PRODUCTO:'), write(Producto), nl,
    forall(
        es_un_transitivo(Producto, Categoria),
        (write('CATEGORIA:'), write(Categoria), nl)
    ),
    forall(
        tiene_propiedad(Producto, Propiedad),
        (write('PROPIEDAD:'), write(Propiedad), nl)
    ),
    forall(
        recomendar_accesorio(Producto, Accesorio),
        (write('ACCESORIO:'), write(Accesorio), nl)
    ).

% exportar_red/0 imprime todos los arcos de la red semantica
% (es_un, propiedad, compatible) en lineas "TIPO:origen:destino",
% para que el orquestador Python pueda dibujar el grafo completo.
exportar_red :-
    forall(es_un(X, Y),      (write('ES_UN:'), write(X), write(':'), write(Y), nl)),
    forall(propiedad(X, P),  (write('PROPIEDAD:'), write(X), write(':'), write(P), nl)),
    forall(compatible(X, A), (write('COMPATIBLE:'), write(X), write(':'), write(A), nl)).

% entrada/0 es el punto de entrada real cuando este archivo se
% ejecuta desde el orquestador Python (carpeta python/): si se
% recibe un argumento de linea de comandos (despues de "--") se
% interpreta como nombre de producto y se llama a consultar/1; si
% no se recibe ningun argumento se preserva el comportamiento
% original del modulo, ejecutando la demo de main/0 (para poder
% seguir corriendo este archivo de forma independiente).
entrada :-
    current_prolog_flag(argv, Argv),
    (   Argv = ['__red__'|_]
    ->  exportar_red
    ;   Argv = [ProductoArg|_]
    ->  atom_string(Producto, ProductoArg),
        consultar(Producto)
    ;   main
    ).

:- initialization(entrada, main).
