package com.upao.petsnature.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;

@Entity(name = "Medicamento")
@Table(name = "medicamentos")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Medicamento {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "nombre_medicamento")
    private String nombre;
    private String descripcion;
    @Column(name = "tipo", length = 50)
    @Enumerated(EnumType.STRING)
    private TipoMedicamento tipo;
    @Column(name = "fecha_medicamento", columnDefinition = "DATE", nullable = true)
    private LocalDate fecha; // Fecha de aplicación de la vacuna
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "evento_id")
    private Evento evento;
}
