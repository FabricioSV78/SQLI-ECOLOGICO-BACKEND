package com.upao.petsnature.web.controller;

import com.upao.petsnature.domain.dto.mascotaDto.DatosActualizarMascota;
import com.upao.petsnature.domain.dto.mascotaDto.DatosDetallesMascota;
import com.upao.petsnature.domain.dto.mascotaDto.DatosListadoMascota;
import com.upao.petsnature.domain.dto.mascotaDto.DatosRegistrarMascota;
import com.upao.petsnature.domain.entity.Mascota;
import com.upao.petsnature.infra.repository.UsuarioRepository;
import com.upao.petsnature.services.impl.MascotaServiceImpl;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/mascota")
@CrossOrigin("*")
@RequiredArgsConstructor
public class MascotaController {

    @Autowired
    private MascotaServiceImpl mascotaService;

    @PostMapping("/agregar")
    public ResponseEntity<String> agregarMascota(@RequestParam("nombreMascota") String nombreMascota,
                                                 @RequestParam("fechaNacimiento") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate fechaNacimiento,
                                                 @RequestParam("peso") float peso,
                                                 @RequestParam("alimentacion") String alimentacion,
                                                 @RequestParam("color") String color,
                                                 @RequestParam("detalles") String detalles,
                                                 @RequestParam("razaId") Long razaId,
                                                 @RequestParam("fotoMascota") MultipartFile fotoMascota) {
        try {
            String imagenPath = mascotaService.guardarImagen(fotoMascota);
            DatosRegistrarMascota datosMascota = new DatosRegistrarMascota(nombreMascota, imagenPath, fechaNacimiento, peso, alimentacion, color, detalles, razaId);
            mascotaService.agregarMascota(datosMascota);
            return ResponseEntity.ok("Mascota agregada correctamente");
        } catch (IllegalStateException | IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error interno del servidor: " + e.getMessage());
        }
    }

    @PutMapping("/modificar/{mascotaId}")
    public ResponseEntity<DatosListadoMascota> modificarMascota(@PathVariable Long mascotaId,
                                                                @RequestParam("nombreMascota") Optional<String> nombreMascota,
                                                                @RequestParam("fechaNacimiento") @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) Optional<LocalDate> fechaNacimiento,
                                                                @RequestParam("peso") Optional<Float> peso,
                                                                @RequestParam("alimentacion") Optional<String> alimentacion,
                                                                @RequestParam("color") Optional<String> color,
                                                                @RequestParam("detalles") Optional<String> detalles,
                                                                @RequestParam(value = "fotoMascota", required = false) MultipartFile fotoMascota) throws IOException {
        try {
            DatosActualizarMascota datos = new DatosActualizarMascota(
                    nombreMascota.orElse(null),
                    fotoMascota != null ? mascotaService.guardarImagen(fotoMascota) : null,
                    fechaNacimiento.orElse(null),
                    peso.orElse(null),
                    alimentacion.orElse(null),
                    color.orElse(null),
                    detalles.orElse(null)
            );

            Mascota mascotaActualizada = mascotaService.modificarMascota(mascotaId, datos);
            DatosListadoMascota datosListado = new DatosListadoMascota(mascotaActualizada);
            return ResponseEntity.ok(datosListado);
        } catch (EntityNotFoundException e) {
            return ResponseEntity.notFound().build();
        }
    }


    @GetMapping("/listar")
    public ResponseEntity<List<DatosDetallesMascota>> obtenerDetallesMascotasPorUsuario() {
        List<Mascota> mascotas = mascotaService.obtenerMascotasPorUsuario();
        List<DatosDetallesMascota> detallesMascotas = mascotas.stream()
                .map(DatosDetallesMascota::new)
                .collect(Collectors.toList());

        return ResponseEntity.ok(detallesMascotas);
    }

    @GetMapping("/por-raza")
    public ResponseEntity<List<DatosDetallesMascota>> obtenerMascotasPorRaza(@RequestParam Long razaId) {
        try {
            List<Mascota> mascotas = mascotaService.obtenerMascotasPorRaza(razaId);
            List<DatosDetallesMascota> detallesMascotas = mascotas.stream()
                    .map(DatosDetallesMascota::new)
                    .collect(Collectors.toList());
            return ResponseEntity.ok(detallesMascotas);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(null);
        }
    }
}
