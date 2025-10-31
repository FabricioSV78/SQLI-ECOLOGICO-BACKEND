package com.upao.petsnature.domain.entity;

import com.upao.petsnature.domain.dto.mascotaDto.DatosActualizarMascota;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.Set;

@Entity(name = "Mascota")
@Table(name = "mascotas")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Mascota {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "nombre_mascota")
    private String nombre;
    @Lob
    @Column(columnDefinition = "MEDIUMTEXT", name = "foto_mascota")
    private String foto;
    @Column(name = "fecha_nacimiento", columnDefinition = "DATE")
    private LocalDate fecha;
    private float peso;
    private String alimentacion;
    private String color;
    private String detalles;
    private boolean enabled = true;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "usuario_id")
    private Usuario usuario;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "raza_id")
    private Raza raza;
    @OneToMany(mappedBy = "mascota", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private Set<Evento> evento;

    public void actualizarMascota(DatosActualizarMascota datosActualizarMascota){
        if (datosActualizarMascota.nombreMascota() != null && !datosActualizarMascota.nombreMascota().isBlank()){
            this.nombre = datosActualizarMascota.nombreMascota();
        }
        if (datosActualizarMascota.fotoMascota() != null && !datosActualizarMascota.fotoMascota().isBlank()){
            this.foto = datosActualizarMascota.fotoMascota();
        }
        if (datosActualizarMascota.fechaNacimiento() != null){
            this.fecha = datosActualizarMascota.fechaNacimiento();
        }
        if (datosActualizarMascota.peso() != null){
            this.peso = datosActualizarMascota.peso();
        }
        if (datosActualizarMascota.alimentacion() != null && !datosActualizarMascota.alimentacion().isBlank()){
            this.alimentacion = datosActualizarMascota.alimentacion();
        }
        if (datosActualizarMascota.color() != null && !datosActualizarMascota.color().isBlank()){
            this.color = datosActualizarMascota.color();
        }
        if (datosActualizarMascota.detalles() != null && !datosActualizarMascota.detalles().isBlank()){
            this.detalles = datosActualizarMascota.detalles();
        }

    }


}
