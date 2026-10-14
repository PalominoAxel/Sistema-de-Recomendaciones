% ============================================================
% MOTOR DE RECOMENDACION PARA E-COMMERCE
% MODULO LOGICO (PROLOG) - RED SEMANTICA E INFERENCIA
% ------------------------------------------------------------
% Responsabilidad de este modulo: representar el conocimiento
% sobre el catalogo (jerarquia de productos, propiedades y
% compatibilidades) como una Red Semantica, e inferir sobre
% ella: herencia transitiva de categorias/propiedades y
% recomendacion de accesorios compatibles.
%
% Los hechos es_un/2 marcados como "instancias del catalogo"
% son los que, en la arquitectura completa, genera el Modulo
% Scala 
%
% Compatible con GNU Prolog / OneCompiler (ejecucion por lotes
% con main/0 e :- initialization(main)).
% ============================================================


es_un(laptop,      electronica).
es_un(smartphone,  electronica).
es_un(camisa,      ropa).
es_un(pantalon,    ropa).
es_un(electronica, producto).
es_un(ropa,        producto).

es_un(laptop_hp,         laptop).
es_un(laptop_asus,       laptop).
es_un(smartphone_sams,   smartphone).
es_un(smartphone_xiaomi, smartphone).
es_un(camisa_polo,       camisa).
es_un(pantalon_jean,     pantalon).

propiedad(producto,    tiene_precio).
propiedad(electronica, requiere_electricidad).
propiedad(laptop,      portatil).
propiedad(smartphone,  portatil).
propiedad(ropa,        textil).


compatible(laptop,     mouse).
compatible(laptop,     funda_laptop).
compatible(laptop,     audifonos).
compatible(smartphone, funda_smartphone).
compatible(smartphone, cargador_rapido).
compatible(smartphone, audifonos).
compatible(camisa,     corbata).
compatible(pantalon,   cinturon).



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

------------------

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
    ).

:- initialization(main).
