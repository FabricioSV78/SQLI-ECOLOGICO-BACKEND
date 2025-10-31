package com.upao.petsnature.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.Set;

@Entity(name = "TipoMascota")
@Table(name = "tipos_mascotas")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class TipoMascota {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String nombre;
    @OneToMany(mappedBy = "tipoMascota", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private Set<Raza> raza;
}
