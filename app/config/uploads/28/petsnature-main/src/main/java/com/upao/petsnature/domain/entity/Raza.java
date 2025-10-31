package com.upao.petsnature.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.Set;

@Entity(name = "Raza")
@Table(name = "razas")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Raza {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String nombre;
    @OneToMany(mappedBy = "raza", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private Set<Mascota> mascota;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tipo_mascota_id")
    private TipoMascota tipoMascota;
    @OneToMany(mappedBy = "raza", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private Set<Consejo> consejo;
}
