package com.upao.petsnature.services.impl;

import com.upao.petsnature.domain.dto.mascotaDto.DatosActualizarMascota;
import com.upao.petsnature.domain.dto.mascotaDto.DatosRegistrarMascota;
import com.upao.petsnature.domain.entity.Mascota;
import com.upao.petsnature.domain.entity.Raza;
import com.upao.petsnature.domain.entity.TipoMascota;
import com.upao.petsnature.domain.entity.Usuario;
import com.upao.petsnature.infra.repository.MascotaRepository;
import com.upao.petsnature.infra.repository.RazaRepository;
import com.upao.petsnature.infra.repository.UsuarioRepository;
import com.upao.petsnature.services.MascotaService;
import jakarta.persistence.EntityNotFoundException;
import jakarta.transaction.Transactional;
import org.apache.tomcat.util.codec.binary.Base64;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Set;

@Service
public class MascotaServiceImpl implements MascotaService {

    @Autowired
    private UsuarioRepository usuarioRepository;

    @Autowired
    private MascotaRepository mascotaRepository;

    private static final List<String> FORMATOS_PERMITIDOS = Arrays.asList("image/png", "image/jpeg", "image/jpg");
    private static final long TAMANO_MAXIMO = 5 * 1024 * 1024; // 5MB
    @Autowired
    private RazaRepository razaRepository;

    @Override
    public void agregarMascota(DatosRegistrarMascota datos) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated()) {
            throw new SecurityException("No hay usuario autenticado");
        }

        String username = (String) authentication.getPrincipal();

        Usuario usuario = usuarioRepository.findByUsername(username)
                .orElseThrow(() -> new EntityNotFoundException("Usuario no encontrado" + username));

        Raza raza = razaRepository.findById(datos.razaId())
                    .orElseThrow(() -> new EntityNotFoundException("Raza no encontrada: " + datos.razaId()));

        if(!usuario.puedeAgregarMascota()){
            throw new IllegalStateException("No puedes agregar más de 10 mascotas");
        }

        Mascota mascota = new Mascota();
        mascota.setNombre(datos.nombreMascota());
        mascota.setFoto(datos.fotoMascota());
        mascota.setFecha(datos.fechaNacimiento());
        mascota.setPeso(datos.peso());
        mascota.setAlimentacion(datos.alimentacion());
        mascota.setColor(datos.color());
        mascota.setDetalles(datos.detalles());
        mascota.setRaza(raza);
        mascota.setUsuario(usuario);

        mascotaRepository.save(mascota);
    }

    @Override
    public String guardarImagen(MultipartFile imagen) throws IOException {
        if (!imagen.isEmpty()) {
            if (!FORMATOS_PERMITIDOS.contains(imagen.getContentType())) {
                throw new IllegalArgumentException("Formato de archivo no permitido.");
            }
            if (imagen.getSize() > TAMANO_MAXIMO) {
                throw new IllegalArgumentException("El archivo excede el tamaño máximo permitido.");
            }

            byte[] bytes = imagen.getBytes();
            return Base64.encodeBase64String(bytes);
        }
        return null;
    }

    @Override
    public Mascota modificarMascota(Long mascotaId, DatosActualizarMascota datos) {
        Mascota mascota = mascotaRepository.findById(mascotaId)
                .orElseThrow(() -> new EntityNotFoundException("Mascota no encontrada con ID: " + mascotaId));

        mascota.actualizarMascota(datos);

        return mascotaRepository.save(mascota);
    }

    @Override
    public List<Mascota> obtenerMascotasPorUsuario() {
        String username = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        Usuario usuario = usuarioRepository.findByUsername(username)
                .orElseThrow(() -> new EntityNotFoundException("Usuario no encontrado: " + username));
        return mascotaRepository.findByUsuarioId(usuario.getId());
    }

    @Override
    public List<Mascota> obtenerMascotasPorRaza(Long razaId) {
        return mascotaRepository.findByRazaId(razaId);
    }

}
