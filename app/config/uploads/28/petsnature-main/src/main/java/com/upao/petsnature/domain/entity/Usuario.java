package com.upao.petsnature.domain.entity;

import com.upao.petsnature.domain.dto.usuarioDto.DatosActualizarUsuario;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.List;
import java.util.Set;

@Entity(name = "Usuario")
@Table(name = "usuarios", uniqueConstraints = {@UniqueConstraint(columnNames = {"username"})})
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Usuario implements UserDetails {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String nombre;
    private String apellido;
    private String dni;
    @Column(unique = true)
    private String telefono;
    @Column(unique = true)
    private String correo;
    @Column(name = "usuario")
    private String username;
    @Column(name = "contraseña")
    private String password;
    @Enumerated(EnumType.STRING)
    private Rol rol;
    @Column(updatable  = false)
    @CreationTimestamp
    private LocalDateTime fechaCreacion;
    @UpdateTimestamp
    private LocalDateTime fechaActualizacion;
    @Column(nullable = false, name = "estado")
    private boolean enabled = true;
    @OneToMany(mappedBy = "usuario", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    private Set<Mascota> mascota;

    public boolean puedeAgregarMascota(){
        return mascota.size() < 10;
    }

    public void actualizarUsuario(DatosActualizarUsuario datosActualizarUsuario){
        if (datosActualizarUsuario.nombre() != null){
            this.nombre = datosActualizarUsuario.nombre();
        }
        if (datosActualizarUsuario.apellido() != null){
            this.apellido = datosActualizarUsuario.apellido();
        }
        if (datosActualizarUsuario.telefono() != null){
            this.telefono = datosActualizarUsuario.telefono();
        }
        if (datosActualizarUsuario.correo() != null){
            this.correo = datosActualizarUsuario.correo();
        }
        if (datosActualizarUsuario.username() != null){
            this.username = datosActualizarUsuario.username();
        }
        if (datosActualizarUsuario.dni() != null){
            this.telefono = datosActualizarUsuario.dni();
        }
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_" + rol.name()));
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return this.enabled;
    }

}
