package com.upao.petsnature.services;

import com.upao.petsnature.domain.dto.mascotaDto.DatosActualizarMascota;
import com.upao.petsnature.domain.dto.mascotaDto.DatosRegistrarMascota;
import com.upao.petsnature.domain.entity.Mascota;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

public interface MascotaService {

    public void agregarMascota(DatosRegistrarMascota datos);

    public String guardarImagen(MultipartFile imagen) throws IOException;

    public Mascota modificarMascota(Long mascotaId, DatosActualizarMascota datos);

    public List<Mascota> obtenerMascotasPorUsuario();

    public List<Mascota> obtenerMascotasPorRaza(Long razaId);
}
