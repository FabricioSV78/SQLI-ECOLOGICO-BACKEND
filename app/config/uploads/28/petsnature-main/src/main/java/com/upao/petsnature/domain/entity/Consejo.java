package com.upao.petsnature.domain.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity(name = "Consejo")
@Table(name = "consejos")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Consejo {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String texto;
    private String edad;
    private float peso;
    private String alimentacion;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "raza_id")
    private Raza raza;
}
