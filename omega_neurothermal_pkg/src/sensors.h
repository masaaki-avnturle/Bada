/* sensors.h
 *
 * 赤外線センサーと温度計の装置機能（シミュレーション）。
 * Infrared (Stefan-Boltzmann radiometric) sensor and contact thermometer models,
 * with simple sensor-fusion of the two readings.
 */
#ifndef OMEGA_SENSORS_H
#define OMEGA_SENSORS_H

/* Stefan-Boltzmann 定数 [W m^-2 K^-4] */
#define OM_SIGMA 5.670374419e-8

/* 赤外線センサー: 放射輝度から物体温度を推定する。
 *   M = ε σ T^4  (T はケルビン)
 * 返り値は推定温度[°C]。emissivity ε は 0..1。ambient_c は背景温度[°C]。 */
double ir_sensor_read(double object_temp_c, double emissivity,
                      double ambient_c, double noise_sigma, unsigned *seed);

/* 接触式温度計: 真値に正規ノイズと一次遅れ(なまり)を加えた読み。
 *   prev は前回読み値[°C]（一次遅れ用、初回は真値を渡す）。 */
double thermometer_read(double true_temp_c, double prev, double tau,
                        double noise_sigma, unsigned *seed);

/* 2系統のセンサー融合（逆分散加重平均）。
 *   各読み値とその分散を与え、加重平均と融合分散を返す。 */
double sensor_fuse(double ir_c, double ir_var,
                   double th_c, double th_var, double *fused_var);

#endif /* OMEGA_SENSORS_H */
